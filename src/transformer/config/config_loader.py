"""Shared, versioned YAML config loader for the confidence and validation engines.

Per Sprint 06/07 design: callers never read YAML directly and engines never
hold a reference to the loader itself.  A ``ConfigLoader`` instance is
constructed once (typically in CLI/pipeline wiring), used to ``load()`` an
immutable ``Config`` object, and that object -- not the loader -- is what
gets injected into ``ConfidenceEngine`` / ``ValidationEngine``.

The loader is intentionally NOT a process-wide singleton or module-level
cache: each ``ConfigLoader`` instance caches results for its own lifetime
only (keyed by resolved path + expected schema version), which keeps
behaviour predictable across test runs -- a fresh ``ConfigLoader()`` in each
test gets a fresh cache, so no test can leak stale config into another.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from transformer.config.exceptions import ConfigError
from transformer.config.loader import load_yaml
from transformer.normalizers.exceptions import NormalizationError

# Schema version this codebase knows how to read. Config files must declare
# a `version` between `minimum_supported_version` and `current_version`.
CURRENT_SCHEMA_VERSION = "1.0"
MINIMUM_SUPPORTED_SCHEMA_VERSION = "1.0"


class Config(BaseModel):
    """Immutable, validated configuration loaded from a single YAML file.

    Attributes:
        version: Schema version declared by the YAML file.
        path: Resolved filesystem path the config was loaded from.
        data: The raw parsed mapping, excluding the ``version`` key.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str
    path: str
    data: dict[str, Any]

    def section(self, key: str, default: Any = None) -> Any:
        """Read a top-level section from the underlying config data.

        Args:
            key: Top-level mapping key.
            default: Value to return when ``key`` is absent.

        Returns:
            The section value, or ``default`` if not present.
        """
        return self.data.get(key, default)


class ConfigLoader:
    """Loads, validates, and caches YAML config files as immutable ``Config``.

    A single loader instance is shared by whoever wires up the pipeline
    (CLI, tests, etc.) and is used to produce ``Config`` objects that are
    then injected into engines. Engines never see the loader itself.
    """

    def __init__(
        self,
        *,
        current_version: str = CURRENT_SCHEMA_VERSION,
        minimum_supported_version: str = MINIMUM_SUPPORTED_SCHEMA_VERSION,
    ) -> None:
        """Initialise the loader with the schema version range it accepts.

        Args:
            current_version: Latest schema version this code understands.
            minimum_supported_version: Oldest schema version still accepted.
        """
        self._current_version = current_version
        self._minimum_supported_version = minimum_supported_version
        self._cache: dict[Path, Config] = {}

    def load(self, path: Path) -> Config:
        """Load a YAML config file into an immutable, version-checked ``Config``.

        Results are cached per resolved path for the lifetime of this loader
        instance only.

        Args:
            path: Path to the YAML config file.

        Returns:
            The immutable, validated ``Config``.

        Raises:
            ConfigError: If the file is missing/invalid, the ``version`` key
                is absent, or the declared version is outside the supported
                range.
        """
        resolved = path.resolve()
        if resolved in self._cache:
            return self._cache[resolved]

        raw = self._load_yaml(resolved)

        version = raw.get("version")
        if not isinstance(version, str) or not version.strip():
            raise ConfigError(
                f"config file is missing a required 'version' key: {resolved}"
            )
        if not (self._minimum_supported_version <= version <= self._current_version):
            raise ConfigError(
                f"unsupported config schema version '{version}' in {resolved} "
                f"(supported range: {self._minimum_supported_version}-"
                f"{self._current_version})"
            )

        data = {k: v for k, v in raw.items() if k != "version"}
        config = Config(version=version, path=str(resolved), data=data)
        self._cache[resolved] = config
        return config

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load raw YAML, normalising any underlying error to ``ConfigError``.

        ``transformer.config.loader.load_yaml`` is a shared helper used by
        several packages and raises ``NormalizationError`` (its own
        package's exception type). ``ConfigLoader`` callers should only ever
        need to catch one exception type, so that gets translated here.

        Args:
            path: Path to the YAML file.

        Returns:
            The parsed top-level mapping.

        Raises:
            ConfigError: If the file is missing/unreadable or not valid YAML.
        """
        try:
            return load_yaml(path)
        except NormalizationError as exc:
            raise ConfigError(exc.message) from exc

    def clear_cache(self) -> None:
        """Drop all cached ``Config`` objects, forcing the next load to re-read."""
        self._cache.clear()
