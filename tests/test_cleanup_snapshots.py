"""Tests for snapshot retention cleanup."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from cleanup_snapshots import delete_old_snapshots


def make_client(snapshots):
    """Build a mock EC2 paginator containing the provided snapshots."""
    client = Mock()
    paginator = Mock()
    paginator.paginate.return_value = [{"Snapshots": snapshots}]
    client.get_paginator.return_value = paginator
    return client


def test_cleanup_deletes_only_expired_snapshots():
    now = datetime(2026, 7, 2, tzinfo=timezone.utc)
    client = make_client(
        [
            {
                "SnapshotId": "snap-old",
                "StartTime": now - timedelta(days=8),
            },
            {
                "SnapshotId": "snap-new",
                "StartTime": now - timedelta(days=2),
            },
        ]
    )

    deleted = delete_old_snapshots(client, 7, "project", now=now)

    assert deleted == ["snap-old"]
    client.delete_snapshot.assert_called_once_with(SnapshotId="snap-old")


def test_cleanup_dry_run_does_not_delete():
    now = datetime(2026, 7, 2, tzinfo=timezone.utc)
    client = make_client(
        [{"SnapshotId": "snap-old", "StartTime": now - timedelta(days=8)}]
    )

    deleted = delete_old_snapshots(
        client, 7, "project", dry_run=True, now=now
    )

    assert deleted == ["snap-old"]
    client.delete_snapshot.assert_not_called()
