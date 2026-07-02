"""Restore a new EBS volume from a snapshot."""

from __future__ import annotations

import argparse
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config_loader import load_config

LOGGER = logging.getLogger(__name__)


def restore_volume(
    ec2_client: Any,
    snapshot_id: str,
    availability_zone: str,
    volume_type: str = "gp3",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Create an EBS volume from a snapshot or simulate the request."""
    if dry_run:
        LOGGER.info(
            "Dry run: volume restore simulated snapshot=%s az=%s",
            snapshot_id,
            availability_zone,
        )
        return {
            "VolumeId": "dry-run-volume",
            "SnapshotId": snapshot_id,
            "AvailabilityZone": availability_zone,
            "State": "dry-run",
        }
    try:
        volume = ec2_client.create_volume(
            SnapshotId=snapshot_id,
            AvailabilityZone=availability_zone,
            VolumeType=volume_type,
            TagSpecifications=[
                {
                    "ResourceType": "volume",
                    "Tags": [
                        {"Key": "RestoredFrom", "Value": snapshot_id},
                        {"Key": "ManagedBy", "Value": "snapshot-manager"},
                    ],
                }
            ],
        )
    except (BotoCoreError, ClientError) as exc:
        LOGGER.exception("Volume restore failed for snapshot %s", snapshot_id)
        raise RuntimeError(
            f"Unable to restore volume from snapshot {snapshot_id}"
        ) from exc
    LOGGER.info(
        "Restored volume %s from snapshot %s",
        volume.get("VolumeId"),
        snapshot_id,
    )
    return volume


def main() -> None:
    """Run the restore operation from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_id", help="Snapshot ID to restore")
    parser.add_argument("--config", help="Path to config.json")
    args = parser.parse_args()
    config = load_config(args.config)
    logging.basicConfig(level=logging.INFO)
    client = boto3.client("ec2", region_name=config["region"])
    restore_volume(
        client,
        args.snapshot_id,
        config["availability_zone"],
        config.get("volume_type", "gp3"),
        bool(config.get("dry_run", False)),
    )


if __name__ == "__main__":
    main()
