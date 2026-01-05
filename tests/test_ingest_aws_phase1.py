"""
Usage:
  pytest tests/test_ingest_aws_phase1.py

Purpose:
  Validate AWS CloudTrail ingestion and normalization behavior.

Limitations:
  - Uses synthetic records; does not cover full CloudTrail schema.
"""

import json
import logging
from pathlib import Path

import pytest

from src.ingest_aws import ingest_cloudtrail


def _base_record() -> dict:
    return {
        "eventID": "abc-123",
        "eventTime": "2020-01-01T00:00:00Z",
        "eventSource": "iam.amazonaws.com",
        "eventName": "CreateUser",
        "sourceIPAddress": "1.2.3.4",
        "userAgent": "console.amazonaws.com",
        "awsRegion": "us-east-1",
        "userIdentity": {
            "type": "IAMUser",
            "arn": "arn:aws:iam::123456789012:user/alice",
            "userName": "alice",
        },
        "resources": [{"ARN": "arn:aws:iam::123456789012:user/alice"}],
    }


def test_jsonl_ingestion(tmp_path: Path) -> None:
    file_path = tmp_path / "events.jsonl"
    record_one = _base_record()
    record_two = {**_base_record(), "eventID": "def-456", "eventName": "DeleteUser"}

    file_path.write_text(
        json.dumps(record_one) + "\n" + "{bad json}\n" + json.dumps(record_two) + "\n",
        encoding="utf-8",
    )

    events = ingest_cloudtrail(file_path)
    assert len(events) == 2
    assert [event["record_index"] for event in events] == [0, 2]


def test_json_records_wrapper(tmp_path: Path) -> None:
    file_path = tmp_path / "events.json"
    payload = {"Records": [_base_record(), {**_base_record(), "eventID": "xyz-789"}]}
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    events = ingest_cloudtrail(file_path)
    assert len(events) == 2
    assert events[0]["record_index"] == 0
    assert events[1]["record_index"] == 1


def test_missing_required_fields(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    file_path = tmp_path / "missing.jsonl"
    missing_time = {**_base_record()}
    missing_time.pop("eventTime")
    file_path.write_text(
        json.dumps(missing_time) + "\n" + json.dumps(_base_record()) + "\n",
        encoding="utf-8",
    )

    events = ingest_cloudtrail(file_path)
    assert len(events) == 1
    assert "missing or empty required field" in caplog.text.lower()


def test_useridentity_null(tmp_path: Path) -> None:
    file_path = tmp_path / "useridentity.jsonl"
    record = {**_base_record(), "userIdentity": None}
    file_path.write_text(json.dumps(record), encoding="utf-8")

    events = ingest_cloudtrail(file_path)
    raw_event = events[0]["raw_event"]
    assert raw_event["actor"] == "SYSTEM"
    assert raw_event["actor_type"] == "Unknown"


def test_no_resources(tmp_path: Path) -> None:
    file_path = tmp_path / "no_resources.jsonl"
    record = {**_base_record()}
    record.pop("resources", None)
    file_path.write_text(json.dumps(record), encoding="utf-8")

    events = ingest_cloudtrail(file_path)
    raw_event = events[0]["raw_event"]
    assert raw_event["resources"] == ["NONE"]


def test_raw_hash_stability(tmp_path: Path) -> None:
    file_path = tmp_path / "hash.jsonl"
    record = _base_record()
    file_path.write_text(
        json.dumps(record) + "\n" + json.dumps(record) + "\n",
        encoding="utf-8",
    )

    events = ingest_cloudtrail(file_path)
    assert events[0]["raw_event"]["raw_hash"] == events[1]["raw_event"]["raw_hash"]
    assert len(events[0]["raw_event"]["raw_hash"]) == 64


def test_error_handling(tmp_path: Path) -> None:
    file_path = tmp_path / "error.jsonl"
    record = {**_base_record(), "errorCode": "AccessDenied", "errorMessage": "Denied"}
    file_path.write_text(json.dumps(record), encoding="utf-8")

    events = ingest_cloudtrail(file_path)
    raw_event = events[0]["raw_event"]
    assert raw_event["error"] == "AccessDenied: Denied"
