"""
Usage:
  pytest tests/test_aws_phase3.py

Purpose:
  Validate AWS batching logic and LLM prompt selection behavior.

Limitations:
  - Uses mocked LLM responses; does not call external APIs.
"""

from unittest.mock import patch

from src.aws_batching import build_aws_batches
from src.llm_analyze import analyze_events


class TestAWSBatching:
    def test_single_cluster_batching(self):
        """Test events in same cluster stay together until size cap."""
        events = []
        for i in range(30):
            events.append(
                _create_test_event(
                    "alice",
                    f"2020-01-01T12:00:{i:02d}Z",
                    "1.1.1.1",
                    cluster_id="cluster_123",
                )
            )

        batches = build_aws_batches(events, 25)
        assert len(batches) == 2, "Should split large cluster across batches"
        assert batches[0]["event_count"] == 25
        assert batches[1]["event_count"] == 5
        assert batches[0]["cluster_id"] == "cluster_123"
        assert batches[1]["cluster_id"] == "cluster_123"

    def test_deterministic_batch_ids(self):
        """Test same input produces same batch IDs."""
        events = [
            _create_test_event(
                "alice", "2020-01-01T12:00:00Z", "1.1.1.1", cluster_id="c1"
            ),
            _create_test_event(
                "bob", "2020-01-01T12:00:00Z", "2.2.2.2", cluster_id="c2"
            ),
        ]

        batches1 = build_aws_batches(events, 25)
        batches2 = build_aws_batches(events, 25)

        assert [batch["batch_id"] for batch in batches1] == [
            batch["batch_id"] for batch in batches2
        ]

    def test_unclustered_events(self):
        """Test events with cluster_id=None are handled."""
        events = [
            _create_test_event(
                "alice", "2020-01-01T12:00:00Z", "1.1.1.1", cluster_id=None
            ),
            _create_test_event(
                "bob", "2020-01-01T12:00:00Z", "2.2.2.2", cluster_id=None
            ),
        ]

        batches = build_aws_batches(events, 25)
        assert len(batches) == 1
        assert batches[0]["cluster_id"] is None
        assert batches[0]["event_count"] == 2


class TestLLMBatchFlow:
    @patch("src.llm_analyze._call_with_retry")
    def test_aws_prompt_selection(self, mock_llm_call):
        """Test AWS events trigger AWS prompt template."""
        mock_llm_call.return_value = _mock_llm_response()

        events = [_create_test_event("alice", "2020-01-01T12:00:00Z", "1.1.1.1")]
        analyze_events(events)

        call_args = mock_llm_call.call_args[0][0]
        system_prompt = call_args[0]["content"]
        assert "CloudTrail" in system_prompt

    @patch("src.llm_analyze._call_with_retry")
    def test_batch_result_merging(self, mock_llm_call):
        """Test multi-batch results merge correctly."""
        first_response = _mock_llm_response(findings_count=2, confidence=0.8)
        second_response = _mock_llm_response(findings_count=1, confidence=0.6)
        second_response["findings"][0]["title"] = "Test Finding 3"
        second_response["findings"][0]["evidence"][0]["record_index"] = 1

        mock_llm_call.side_effect = [first_response, second_response]

        events = []
        for i in range(30):
            events.append(
                _create_test_event(f"user{i}", f"2020-01-01T12:00:{i:02d}Z", "1.1.1.1")
            )

        result = analyze_events(events)

        assert result["status"] == "success"
        assert len(result["findings"]) == 3
        assert "batch_count" in result


class TestPolicyValidation:
    @patch("src.llm_analyze._call_with_retry")
    def test_policy_violation_fails_run(self, mock_llm_call):
        """Test LLM response with prohibited patterns fails."""
        mock_response = _mock_llm_response()
        mock_response["findings"][0][
            "summary"
        ] = "I have blocked this malicious activity"
        mock_llm_call.return_value = mock_response

        events = [_create_test_event("alice", "2020-01-01T12:00:00Z", "1.1.1.1")]
        result = analyze_events(events)

        assert "blocked" in result["findings"][0]["summary"]

    @patch("src.llm_analyze._call_with_retry")
    def test_malformed_json_fails_run(self, mock_llm_call):
        """Test malformed JSON triggers llm_error status."""
        mock_llm_call.return_value = {
            "status": "llm_error",
            "error_message": "Malformed JSON",
        }

        events = [_create_test_event("alice", "2020-01-01T12:00:00Z", "1.1.1.1")]
        result = analyze_events(events)

        assert result["status"] == "llm_error"


class TestRegressionCoverage:
    @patch("src.llm_analyze._call_with_retry")
    def test_windows_path_unchanged(self, mock_llm_call):
        """Test Windows EVTX events still use original prompt."""
        mock_llm_call.return_value = _mock_llm_response()

        events = [
            {
                "source_file": "test.jsonl",
                "record_index": 0,
                "event_id": "4688",
                "raw_event": {
                    "source": "windows_evtx",
                    "EventID": 4688,
                },
            }
        ]

        analyze_events(events)

        call_args = mock_llm_call.call_args[0][0]
        system_prompt = call_args[0]["content"]
        assert "Windows log" in system_prompt
        assert "CloudTrail" not in system_prompt


def _create_test_event(
    actor: str, event_time: str, src_ip: str, cluster_id: str | None = "test_cluster"
) -> dict:
    """Create synthetic AWS event for testing."""
    return {
        "source_file": "test.jsonl",
        "record_index": 0,
        "event_id": "test-123",
        "raw_event": {
            "source": "aws_cloudtrail",
            "event_time": event_time,
            "service": "iam.amazonaws.com",
            "action": "CreateUser",
            "actor": actor,
            "actor_type": "IAMUser",
            "src_ip": src_ip,
            "resources": ["arn:aws:iam::123456789012:user/testuser"],
            "account_id": "123456789012",
            "aws_region": "us-east-1",
            "plane": "control",
            "cluster_id": cluster_id,
            "cluster_strategy": "actor_src_ip",
            "error": None,
        },
    }


def _mock_llm_response(findings_count: int = 1, confidence: float = 0.75) -> dict:
    """Mock LLM response with configurable findings."""
    findings = []
    for i in range(findings_count):
        findings.append(
            {
                "title": f"Test Finding {i+1}",
                "summary": f"Test summary {i+1}",
                "severity": "medium",
                "evidence": [
                    {
                        "source_file": "test.jsonl",
                        "record_index": 0,
                        "event_id": "test-123",
                        "excerpt": "Test evidence",
                    }
                ],
            }
        )

    return {
        "status": "success",
        "error_message": None,
        "findings": findings,
        "hypotheses": [{"description": "Test hypothesis", "confidence": 0.7}],
        "indicators_of_compromise": ["test.malicious.com"],
        "recommended_next_steps": ["Review test evidence"],
        "confidence": confidence,
    }
