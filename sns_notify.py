"""Amazon SNS notifications for snapshot operations."""

from __future__ import annotations

import logging
from typing import Any, Dict

from botocore.exceptions import BotoCoreError, ClientError

LOGGER = logging.getLogger(__name__)


def send_snapshot_notification(
    sns_client: Any,
    topic_arn: str,
    snapshot: Dict[str, Any],
    project_name: str,
) -> bool:
    """Publish a snapshot-created notification to SNS.

    A blank topic ARN disables notifications without treating that as an error.
    """
    if not topic_arn:
        LOGGER.info("SNS notification skipped: no topic ARN configured")
        return False

    snapshot_id = snapshot.get("SnapshotId", "unknown")
    volume_id = snapshot.get("VolumeId", "unknown")
    message = (
        f"Project: {project_name}\n"
        f"Snapshot: {snapshot_id}\n"
        f"Volume: {volume_id}\n"
        f"Status: {snapshot.get('State', 'unknown')}\n"
        f"Creation time: {snapshot.get('StartTime', 'unknown')}"
    )
    try:
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=f"EBS snapshot created: {volume_id}",
            Message=message,
        )
    except (BotoCoreError, ClientError) as exc:
        LOGGER.exception(
            "SNS notification failed for snapshot %s", snapshot_id
        )
        raise RuntimeError(
            f"Unable to send SNS notification for snapshot {snapshot_id}"
        ) from exc

    LOGGER.info("SNS notification sent for snapshot %s", snapshot_id)
    return True
