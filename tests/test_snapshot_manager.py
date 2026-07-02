"""Tests for snapshot manager orchestration."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from snapshot_manager import run_snapshot_manager


def base_config(tmp_path):
    """Return a complete test configuration."""
    return {
        "region": "ap-south-1",
        "retention_days": 7,
        "volumes": ["vol-one", "vol-two"],
        "project_name": "test-project",
        "sns_topic_arn": "arn:aws:sns:ap-south-1:123456789012:test",
        "dry_run": False,
        "report_path": str(tmp_path / "report.csv"),
    }


@patch("snapshot_manager.delete_old_snapshots", return_value=["snap-old"])
@patch("snapshot_manager.send_snapshot_notification")
@patch("snapshot_manager.create_snapshot")
def test_manager_processes_multiple_volumes(
    create_mock, notify_mock, cleanup_mock, tmp_path
):
    create_mock.side_effect = [
        {
            "SnapshotId": "snap-one",
            "VolumeId": "vol-one",
            "StartTime": datetime.now(timezone.utc),
            "State": "pending",
            "Description": "one",
        },
        {
            "SnapshotId": "snap-two",
            "VolumeId": "vol-two",
            "StartTime": datetime.now(timezone.utc),
            "State": "pending",
            "Description": "two",
        },
    ]

    result = run_snapshot_manager(base_config(tmp_path), Mock(), Mock())

    assert result["status"] == "success"
    assert result["created_snapshot_ids"] == ["snap-one", "snap-two"]
    assert create_mock.call_count == 2
    assert notify_mock.call_count == 2
    cleanup_mock.assert_called_once()


@patch("snapshot_manager.delete_old_snapshots", return_value=[])
@patch("snapshot_manager.create_snapshot")
def test_manager_isolates_volume_failure(create_mock, cleanup_mock, tmp_path):
    create_mock.side_effect = [
        RuntimeError("first failed"),
        {
            "SnapshotId": "snap-two",
            "VolumeId": "vol-two",
            "StartTime": datetime.now(timezone.utc),
            "State": "pending",
            "Description": "two",
        },
    ]
    config = base_config(tmp_path)
    config["sns_topic_arn"] = ""

    result = run_snapshot_manager(config, Mock())

    assert result["status"] == "partial_failure"
    assert result["created_snapshot_ids"] == ["snap-two"]
    assert result["errors"] == ["first failed"]
    cleanup_mock.assert_called_once()
