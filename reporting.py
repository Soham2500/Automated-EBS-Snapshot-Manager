"""CSV reporting utilities for snapshot activity."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable

REPORT_FIELDS = [
    "Snapshot ID",
    "Volume ID",
    "Creation Time",
    "Status",
    "Description",
]


def _serialize_time(value: Any) -> str:
    """Convert AWS datetime values into ISO-8601 report strings."""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "")


def append_snapshot_report(
    snapshots: Iterable[Dict[str, Any]], report_path: str | Path
) -> Path:
    """Append snapshot records to a CSV file, creating its header if needed."""
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=REPORT_FIELDS)
        if write_header:
            writer.writeheader()
        for snapshot in snapshots:
            writer.writerow(
                {
                    "Snapshot ID": snapshot.get("SnapshotId", ""),
                    "Volume ID": snapshot.get("VolumeId", ""),
                    "Creation Time": _serialize_time(
                        snapshot.get("StartTime")
                    ),
                    "Status": snapshot.get("State", "unknown"),
                    "Description": snapshot.get("Description", ""),
                }
            )
    return path
