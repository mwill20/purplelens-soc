"""
Usage:
  pytest tests/test_aws_phase2.py

Purpose:
  Validate AWS plane tagging and correlation clustering.

Limitations:
  - Uses synthetic events; correlation is proximity-based, not causality.
"""

from src.aws_correlate import correlate_events
from src.aws_plane_tagging import tag_plane
from src.config_aws import CORRELATION_CONFIG


class TestPlaneTagging:
    def test_control_plane_services(self):
        assert tag_plane("iam.amazonaws.com", "CreateUser") == "control"
        assert tag_plane("sts.amazonaws.com", "AssumeRole") == "control"
        assert tag_plane("organizations.amazonaws.com", "CreateAccount") == "control"
        assert tag_plane("kms.amazonaws.com", "CreateKey") == "control"

    def test_cloudtrail_logging_blind_actions(self):
        assert tag_plane("cloudtrail.amazonaws.com", "StopLogging") == "control"
        assert tag_plane("cloudtrail.amazonaws.com", "DeleteTrail") == "control"
        assert tag_plane("cloudtrail.amazonaws.com", "UpdateTrail") == "control"
        assert tag_plane("cloudtrail.amazonaws.com", "PutEventSelectors") == "control"
        assert tag_plane("cloudtrail.amazonaws.com", "CreateTrail") == "control"

    def test_telemetry_plane(self):
        assert tag_plane("logs.amazonaws.com", "PutRetentionPolicy") == "telemetry"
        assert tag_plane("cloudwatch.amazonaws.com", "PutMetricData") == "telemetry"
        assert tag_plane("events.amazonaws.com", "PutRule") == "telemetry"

    def test_data_plane_s3(self):
        assert tag_plane("s3.amazonaws.com", "GetObject") == "data"
        assert tag_plane("s3.amazonaws.com", "PutObject") == "data"
        assert tag_plane("s3.amazonaws.com", "DeleteObject") == "data"
        assert tag_plane("s3.amazonaws.com", "ListBucket") == "data"
        assert tag_plane("s3.amazonaws.com", "CreateBucket") == "unknown"

    def test_data_plane_dynamodb(self):
        assert tag_plane("dynamodb.amazonaws.com", "GetItem") == "data"
        assert tag_plane("dynamodb.amazonaws.com", "PutItem") == "data"
        assert tag_plane("dynamodb.amazonaws.com", "UpdateItem") == "data"
        assert tag_plane("dynamodb.amazonaws.com", "DeleteItem") == "data"
        assert tag_plane("dynamodb.amazonaws.com", "Query") == "data"
        assert tag_plane("dynamodb.amazonaws.com", "Scan") == "data"
        assert tag_plane("dynamodb.amazonaws.com", "CreateTable") == "unknown"

    def test_unknown_fallback(self):
        assert tag_plane("ec2.amazonaws.com", "DescribeInstances") == "unknown"
        assert tag_plane("unknown.service.com", "SomeAction") == "unknown"


class TestCorrelation:
    def test_time_proximity_clustering(self):
        """Test same actor within 4 minutes -> same cluster."""
        events = [
            _create_test_event("alice", "2020-01-01T12:00:00Z", "1.1.1.1", ["res1"]),
            _create_test_event("alice", "2020-01-01T12:03:00Z", "1.1.1.1", ["res2"]),
        ]

        result = correlate_events(events, CORRELATION_CONFIG)
        cluster_ids = [e["raw_event"]["cluster_id"] for e in result]
        assert cluster_ids[0] == cluster_ids[1], "Same actor within 4min should cluster"

    def test_time_boundary_separation(self):
        """Test same actor 6 minutes apart -> different clusters."""
        events = [
            _create_test_event("alice", "2020-01-01T12:00:00Z", "1.1.1.1", ["res1"]),
            _create_test_event("alice", "2020-01-01T12:06:00Z", "1.1.1.1", ["res2"]),
        ]

        result = correlate_events(events, CORRELATION_CONFIG)
        cluster_ids = [e["raw_event"]["cluster_id"] for e in result]
        assert (
            cluster_ids[0] != cluster_ids[1]
        ), "6min gap should create separate clusters"

    def test_strategy_priority(self):
        """Test actor_src_ip beats actor_resource when both match."""
        events = [
            _create_test_event("alice", "2020-01-01T12:00:00Z", "1.1.1.1", ["res1"]),
            _create_test_event("alice", "2020-01-01T12:01:00Z", "1.1.1.1", ["res1"]),
        ]

        result = correlate_events(events, CORRELATION_CONFIG)
        cluster_strategy = result[0]["raw_event"]["cluster_strategy"]
        assert cluster_strategy == "actor_src_ip"

    def test_cluster_size_cap(self):
        """Test 51 events split into multiple clusters."""
        events = []
        for i in range(51):
            events.append(
                _create_test_event("alice", "2020-01-01T12:00:00Z", "1.1.1.1", ["res1"])
            )

        result = correlate_events(events, CORRELATION_CONFIG)
        cluster_ids = set(e["raw_event"]["cluster_id"] for e in result)
        assert len(cluster_ids) >= 2, "51 events should split due to size cap"

    def test_none_resource_strategy_skip(self):
        """Test events with resources=['NONE'] skip actor_resource strategy."""
        events = [
            _create_test_event("alice", "2020-01-01T12:00:00Z", "", ["NONE"]),
            _create_test_event("alice", "2020-01-01T12:01:00Z", "", ["NONE"]),
        ]

        result = correlate_events(events, CORRELATION_CONFIG)
        cluster_strategy = result[0]["raw_event"]["cluster_strategy"]
        assert cluster_strategy == "actor_only"


def _create_test_event(
    actor: str, event_time: str, src_ip: str, resources: list
) -> dict:
    """Create synthetic event envelope for testing."""
    return {
        "source_file": "test.jsonl",
        "record_index": 0,
        "event_id": "test-123",
        "raw_event": {
            "source": "aws_cloudtrail",
            "event_time": event_time,
            "actor": actor,
            "src_ip": src_ip,
            "resources": resources,
            "service": "s3.amazonaws.com",
            "action": "GetObject",
        },
    }
