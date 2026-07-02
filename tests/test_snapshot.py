"""Tests for EBS snapshot creation."""

from unittest.mock import Mock

from snapshot import create_snapshot


def test_create_snapshot_calls_ec2_with_volume_and_tags():
    client = Mock()
    client.create_snapshot.return_value = {
        "SnapshotId": "snap-123",
        "VolumeId": "vol-123",
        "State": "pending",
    }

    result = create_snapshot(client, "vol-123", "test-project")

    assert result["SnapshotId"] == "snap-123"
    call = client.create_snapshot.call_args.kwargs
    assert call["VolumeId"] == "vol-123"
    assert call["TagSpecifications"][0]["ResourceType"] == "snapshot"


def test_create_snapshot_dry_run_does_not_call_aws():
    client = Mock()

    result = create_snapshot(client, "vol-123", "test-project", dry_run=True)

    assert result["State"] == "dry-run"
    assert result["SnapshotId"].startswith("dry-run-")
    client.create_snapshot.assert_not_called()
