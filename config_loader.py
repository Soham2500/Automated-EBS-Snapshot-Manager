"""Configuration loading and validation for the snapshot manager."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.json")


class ConfigurationError(ValueError):
    """Raised when application configuration is missing or invalid."""


def load_config(config_path: str | Path | None = None) -> Dict[str, Any]:
    """Load and validate the JSON configuration file.

    Args:
        config_path: Optional path. ``CONFIG_PATH`` is used when omitted,
            followed by the project-level ``config.json``.

    Returns:
        A validated configuration dictionary.

    Raises:
        ConfigurationError: If the file is missing, malformed, or incomplete.
    """
    path = Path(
        config_path or os.environ.get("CONFIG_PATH", DEFAULT_CONFIG_PATH)
    )
    try:
        with path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except FileNotFoundError as exc:
        message = f"Configuration file not found: {path}"
        raise ConfigurationError(message) from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            "Configuration file contains invalid JSON: "
            f"{path}"
        ) from exc

    required_fields = {
        "region": str,
        "retention_days": int,
        "volumes": list,
        "project_name": str,
    }
    for field, expected_type in required_fields.items():
        value = config.get(field)
        if not isinstance(value, expected_type) or (
            expected_type in (str, list) and not value
        ):
            raise ConfigurationError(
                f"'{field}' must be a non-empty {expected_type.__name__}"
            )

    if config["retention_days"] < 0:
        raise ConfigurationError("'retention_days' cannot be negative")
    valid_volumes = all(
        isinstance(volume, str) and volume for volume in config["volumes"]
    )
    if not valid_volumes:
        raise ConfigurationError(
            "Every entry in 'volumes' must be a volume ID"
        )

    config.setdefault("sns_topic_arn", "")
    config.setdefault("dry_run", False)
    config.setdefault("report_path", "reports/snapshot_report.csv")
    config.setdefault("volume_type", "gp3")
    return config
