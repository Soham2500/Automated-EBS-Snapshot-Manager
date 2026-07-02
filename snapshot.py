"""EBS snapshot creation operations."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from botocore.exceptions import BotoCoreError, ClientError

LOGGER = logging.getLogger(__name__)


def create_snapshot(
    ec2_client: Any,
    volume_id: str,
    project_name: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Create one managed EBS snapshot or simulate it in dry-run mode.

    Args:
        ec2_client: Boto3 EC2 client.
        volume_id: Source EBS volume ID.
        project_name: Project label used in descriptions and resource tags.
        dry_run: Return a simulated result without calling AWS when true.

    Returns:
        The snapshot metadata returned by EC2, or simulated metadata.

    Raises:
        RuntimeError: If the EC2 create-snapshot API call fails.
    """
    description = f"Automated snapshot for {volume_id} ({project_name})"
    if dry_run:
        snapshot = {
            "SnapshotId": f"dry-run-{uuid4().hex[:12]}",
            "VolumeId": volume_id,
            "StartTime": datetime.now(timezone.utc),
            "State": "dry-run",
            "Description": description,
        }
        LOGGER.info(
            "Dry run: snapshot creation simulated for volume %s", volume_id
        )
        return snapshot

    try:
        snapshot = ec2_client.create_snapshot(
            VolumeId=volume_id,
            Description=description,
            TagSpecifications=[
                {
                    "ResourceType": "snapshot",
                    "Tags": [
                        {"Key": "Name", "Value": project_name},
                        {"Key": "Project", "Value": project_name},
                        {"Key": "ManagedBy", "Value": "snapshot-manager"},
                        {"Key": "SourceVolume", "Value": volume_id},
                    ],
                }
            ],
        )
    except (BotoCoreError, ClientError) as exc:
        LOGGER.exception("Snapshot creation failed for volume %s", volume_id)
        raise RuntimeError(
            f"Unable to create snapshot for volume {volume_id}"
        ) from exc

    LOGGER.info(
        "Snapshot %s created for volume %s with status %s",
        snapshot.get("SnapshotId"),
        volume_id,
        snapshot.get("State", "unknown"),
    )
    return snapshot
