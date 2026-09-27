"""Loading and minimal validation for checked-in TOML contracts."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when required project configuration is missing or invalid."""


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"missing file: {path}")

    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}") from exc


def load_project_config(project_root: Path) -> dict[str, dict[str, Any]]:
    config_dir = project_root.resolve() / "config"
    indicators = _load_toml(config_dir / "indicators.toml")
    quality = _load_toml(config_dir / "quality_rules.toml")

    countries = indicators.get("countries")
    configured_indicators = indicators.get("indicators")
    rules = quality.get("rules")

    if not isinstance(countries, dict) or len(countries) != 6:
        raise ConfigError("indicators.toml must define exactly six countries")
    if not isinstance(configured_indicators, dict) or len(configured_indicators) != 3:
        raise ConfigError("indicators.toml must define exactly three indicators")
    if not isinstance(rules, dict) or not rules:
        raise ConfigError("quality_rules.toml must define quality rules")

    return {"indicators": indicators, "quality": quality}

