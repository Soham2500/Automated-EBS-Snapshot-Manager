"""Retention-based cleanup for snapshots owned by this project."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, List

from botocore.exceptions import BotoCoreError, ClientError

LOGGER = logging.getLogger(__name__)


def delete_old_snapshots(
    ec2_client: Any,
    retention_days: int,
    project_name: str,
    dry_run: bool = False,
    now: datetime | None = None,
) -> List[str]:
    """Delete project-managed snapshots older than the retention period.

    Args:
        ec2_client: Boto3 EC2 client.
        retention_days: Maximum snapshot age in days.
        project_name: Value of the ``Project`` ownership tag.
        dry_run: Log deletions without changing AWS resources when true.
        now: Optional UTC time, primarily for deterministic tests.

    Returns:
        Snapshot IDs deleted or selected for simulated deletion.

    Raises:
        RuntimeError: If snapshot discovery fails.
    """
    reference_time = now or datetime.now(timezone.utc)
    cutoff = reference_time - timedelta(days=retention_days)
    try:
        paginator = ec2_client.get_paginator("describe_snapshots")
        pages = paginator.paginate(
            OwnerIds=["self"],
            Filters=[
                {"Name": "tag:Project", "Values": [project_name]},
                {"Name": "tag:ManagedBy", "Values": ["snapshot-manager"]},
            ],
        )
    except (BotoCoreError, ClientError) as exc:
        LOGGER.exception("Unable to discover snapshots for cleanup")
        raise RuntimeError("Unable to list snapshots for cleanup") from exc

    deleted: List[str] = []
    try:
        for page in pages:
            for snapshot in page.get("Snapshots", []):
                snapshot_id = snapshot["SnapshotId"]
                start_time = snapshot["StartTime"]
                if start_time >= cutoff:
                    continue
                if dry_run:
                    LOGGER.info(
                        "Dry run: snapshot %s would be deleted", snapshot_id
                    )
                else:
                    ec2_client.delete_snapshot(SnapshotId=snapshot_id)
                    LOGGER.info("Deleted expired snapshot %s", snapshot_id)
                deleted.append(snapshot_id)
    except (BotoCoreError, ClientError, KeyError, TypeError) as exc:
        LOGGER.exception("Snapshot cleanup failed")
        raise RuntimeError("Unable to complete snapshot cleanup") from exc

    LOGGER.info("Snapshot cleanup completed; selected=%d", len(deleted))
    return deleted
