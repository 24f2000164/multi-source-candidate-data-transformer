"""Loader for the skill alias configuration consumed by
``transformer.normalizers.skill_normalizer``.
"""

from pathlib import Path

from transformer.config.loader import DEFAULT_CONFIG_DIR, load_yaml
from transformer.normalizers.exceptions import NormalizationError

DEFAULT_SKILL_ALIASES_PATH = DEFAULT_CONFIG_DIR / "skill_aliases.yaml"


def load_skill_aliases(path: Path = DEFAULT_SKILL_ALIASES_PATH) -> dict[str, str]:
    """Load the skill alias map from YAML.

    Args:
        path: Path to the skill alias YAML file. Defaults to
            ``config/skill_aliases.yaml`` at the repository root.

    Returns:
        Mapping of lower-cased alias -> canonical skill name.

    Raises:
        NormalizationError: If the file is missing/invalid, or the
            ``aliases`` key is absent or not a mapping of strings.
    """
    data = load_yaml(path)
    aliases = data.get("aliases")
    if not isinstance(aliases, dict):
        raise NormalizationError(
            f"skill alias config must contain a top-level 'aliases' mapping: {path}"
        )
    return {str(key).lower(): str(value) for key, value in aliases.items()}
