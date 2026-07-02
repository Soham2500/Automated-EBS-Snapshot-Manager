"""Flask dashboard for EBS snapshot report metrics."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, render_template

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "snapshot_report.csv"


def read_snapshot_rows(report_path: Path) -> List[Dict[str, str]]:
    """Read snapshot records from the generated CSV report."""
    if not report_path.exists():
        return []
    with report_path.open("r", newline="", encoding="utf-8") as report_file:
        return list(csv.DictReader(report_file))


def build_metrics(rows: List[Dict[str, str]]) -> Dict[str, str | int]:
    """Calculate dashboard summary metrics from report rows."""
    ordered = sorted(
        rows, key=lambda row: row.get("Creation Time", ""), reverse=True
    )
    latest = ordered[0] if ordered else {}
    return {
        "total_snapshots": len(rows),
        "latest_snapshot": latest.get("Snapshot ID", "No snapshots yet"),
        "last_backup_time": latest.get("Creation Time", "Not available"),
        "backup_status": latest.get("Status", "Not available"),
    }


def create_app(report_path: str | Path | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    configured_path = Path(
        report_path or os.environ.get("SNAPSHOT_REPORT_PATH", DEFAULT_REPORT)
    )

    @app.get("/")
    def dashboard() -> str:
        rows = read_snapshot_rows(configured_path)
        return render_template(
            "index.html",
            metrics=build_metrics(rows),
            snapshots=rows[-10:][::-1],
        )

    @app.get("/api/metrics")
    def metrics_api():
        return jsonify(build_metrics(read_snapshot_rows(configured_path)))

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
