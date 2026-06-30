"""Shared helpers for locating and loading YAML configuration files.

Configuration lives in the repository-level ``config/`` directory (sibling
to ``src/``) so it can be edited and reviewed independently of code, per the
Sprint 4/5 requirement to drive merge priorities and skill aliases from
configuration rather than hardcoding them.
"""

from pathlib import Path
from typing import Any

import yaml

from transformer.normalizers.exceptions import NormalizationError

# src/transformer/config/loader.py -> parents[3] is the repository root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_DIR = _REPO_ROOT / "config"


def load_yaml(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file as a dictionary.

    Args:
        path: Path to the YAML file.

    Returns:
        The parsed top-level mapping.

    Raises:
        NormalizationError: If the file is missing, unreadable, not valid
            YAML, or does not contain a top-level mapping.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise NormalizationError(f"could not read config file: {path}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise NormalizationError(f"invalid YAML in config file: {path}") from exc

    if not isinstance(data, dict):
        raise NormalizationError(
            f"config file must contain a top-level mapping: {path}"
        )
    return data
