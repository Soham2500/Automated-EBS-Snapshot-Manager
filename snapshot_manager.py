"""Orchestration and AWS Lambda entry point for EBS snapshot management."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import boto3

from cleanup_snapshots import delete_old_snapshots
from config_loader import load_config
from reporting import append_snapshot_report
from snapshot import create_snapshot
from sns_notify import send_snapshot_notification

LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure application logging for local runs and CloudWatch Logs."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )


def resolve_report_path(configured_path: str) -> str:
    """Use Lambda's writable temporary directory for relative report paths."""
    path = Path(configured_path)
    running_in_lambda = os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    if running_in_lambda and not path.is_absolute():
        return str(Path("/tmp") / path.name)
    return str(path)


def run_snapshot_manager(
    config: Dict[str, Any],
    ec2_client: Any | None = None,
    sns_client: Any | None = None,
) -> Dict[str, Any]:
    """Create configured snapshots, notify, report, and apply retention.

    Each source volume is isolated so one failure does not prevent the
    remaining volumes from being backed up. Cleanup still runs afterward.
    """
    started = time.perf_counter()
    region = config["region"]
    dry_run = bool(config.get("dry_run", False))
    ec2 = ec2_client or boto3.client("ec2", region_name=region)
    sns = sns_client
    if config.get("sns_topic_arn") and not dry_run:
        sns = sns or boto3.client("sns", region_name=region)

    created: List[Dict[str, Any]] = []
    errors: List[str] = []
    for volume_id in config["volumes"]:
        try:
            snapshot = create_snapshot(
                ec2,
                volume_id,
                config["project_name"],
                dry_run=dry_run,
            )
            created.append(snapshot)
            if not dry_run and sns is not None:
                try:
                    send_snapshot_notification(
                        sns,
                        config.get("sns_topic_arn", ""),
                        snapshot,
                        config["project_name"],
                    )
                except RuntimeError as exc:
                    errors.append(str(exc))
        except RuntimeError as exc:
            errors.append(str(exc))

    if created:
        try:
            append_snapshot_report(
                created, resolve_report_path(config["report_path"])
            )
            LOGGER.info("Snapshot report updated with %d row(s)", len(created))
        except OSError as exc:
            LOGGER.exception("Unable to write snapshot report")
            errors.append(f"Unable to write snapshot report: {exc}")

    try:
        deleted = delete_old_snapshots(
            ec2,
            config["retention_days"],
            config["project_name"],
            dry_run=dry_run,
        )
    except RuntimeError as exc:
        errors.append(str(exc))
        deleted = []

    elapsed = time.perf_counter() - started
    status = "success" if not errors else "partial_failure"
    LOGGER.info(
        "Execution complete status=%s created=%d deleted=%d errors=%d "
        "execution_time_seconds=%.3f",
        status,
        len(created),
        len(deleted),
        len(errors),
        elapsed,
    )
    return {
        "status": status,
        "created_snapshot_ids": [item["SnapshotId"] for item in created],
        "deleted_snapshot_ids": deleted,
        "errors": errors,
        "execution_time_seconds": round(elapsed, 3),
        "dry_run": dry_run,
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler invoked by EventBridge Scheduler."""
    del event, context
    configure_logging()
    config = load_config()
    return run_snapshot_manager(config)


if __name__ == "__main__":
    configure_logging()
    run_snapshot_manager(load_config(Path(__file__).with_name("config.json")))
