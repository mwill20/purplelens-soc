"""
Usage:
  pytest tests/test_aws_csv_converter.py

Purpose:
  Validate CloudTrail CSV-to-JSONL conversion helper.

Limitations:
  - Uses temporary files only; does not cover full dataset scale.
"""

import csv
import json
from pathlib import Path

from scripts.aws_csv_to_jsonl import convert_csv_to_jsonl


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_csv_to_jsonl_conversion(tmp_path: Path) -> None:
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.jsonl"

    rows = [
        {
            "eventID": "1",
            "eventTime": "2020-01-01T00:00:00Z",
            "eventSource": "iam.amazonaws.com",
            "eventName": "CreateUser",
            "userIdentitytype": "IAMUser",
        },
        {
            "eventID": "2",
            "eventTime": "2020-01-02T00:00:00Z",
            "eventSource": "sts.amazonaws.com",
            "eventName": "AssumeRole",
            "userIdentitytype": "AssumedRole",
        },
    ]
    _write_csv(input_path, rows)

    stats = convert_csv_to_jsonl(input_path, output_path)
    assert stats["rows_read"] == 2
    assert stats["rows_converted"] == 2
    assert stats["rows_skipped"] == 0

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_useridentity_nesting(tmp_path: Path) -> None:
    input_path = tmp_path / "identity.csv"
    output_path = tmp_path / "identity.jsonl"

    rows = [
        {
            "eventID": "1",
            "eventTime": "2020-01-01T00:00:00Z",
            "eventSource": "iam.amazonaws.com",
            "eventName": "CreateUser",
            "userIdentitytype": "IAMUser",
            "userIdentityarn": "arn:aws:iam::123456789012:user/alice",
        }
    ]
    _write_csv(input_path, rows)

    convert_csv_to_jsonl(input_path, output_path)
    record = json.loads(output_path.read_text(encoding="utf-8").strip())
    assert record["userIdentity"]["type"] == "IAMUser"
    assert record["userIdentity"]["arn"] == "arn:aws:iam::123456789012:user/alice"


def test_missing_fields_handling(tmp_path: Path) -> None:
    input_path = tmp_path / "missing.csv"
    output_path = tmp_path / "missing.jsonl"

    rows = [
        {
            "eventID": "1",
            "eventTime": "",
            "eventSource": "iam.amazonaws.com",
            "eventName": "CreateUser",
        },
        {
            "eventID": "2",
            "eventTime": "2020-01-02T00:00:00Z",
            "eventSource": "sts.amazonaws.com",
            "eventName": "AssumeRole",
        },
    ]
    _write_csv(input_path, rows)

    stats = convert_csv_to_jsonl(input_path, output_path)
    assert stats["rows_read"] == 2
    assert stats["rows_converted"] == 1
    assert stats["rows_skipped"] == 1


def test_output_line_validity(tmp_path: Path) -> None:
    input_path = tmp_path / "valid.csv"
    output_path = tmp_path / "valid.jsonl"

    rows = [
        {
            "eventID": "1",
            "eventTime": "2020-01-01T00:00:00Z",
            "eventSource": "iam.amazonaws.com",
            "eventName": "CreateUser",
        }
    ]
    _write_csv(input_path, rows)

    convert_csv_to_jsonl(input_path, output_path)
    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        json.loads(line)
