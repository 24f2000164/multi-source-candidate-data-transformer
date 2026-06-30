"""Unit tests for transformer.config.skill_aliases."""

from pathlib import Path

import pytest

from transformer.config.skill_aliases import (
    DEFAULT_SKILL_ALIASES_PATH,
    load_skill_aliases,
)
from transformer.normalizers.exceptions import NormalizationError


@pytest.mark.unit
class TestLoadSkillAliases:
    def test_default_path_exists(self) -> None:
        assert DEFAULT_SKILL_ALIASES_PATH.exists()

    def test_default_aliases_load_lowercased(self) -> None:
        aliases = load_skill_aliases()
        assert aliases["js"] == "JavaScript"
        assert aliases["javascript"] == "JavaScript"

    def test_keys_are_lowercased_regardless_of_source_casing(
        self, tmp_path: Path
    ) -> None:
        config = tmp_path / "aliases.yaml"
        config.write_text("aliases:\n  JS: JavaScript\n")
        aliases = load_skill_aliases(config)
        assert aliases["js"] == "JavaScript"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(NormalizationError):
            load_skill_aliases(tmp_path / "missing.yaml")

    def test_missing_aliases_key_raises(self, tmp_path: Path) -> None:
        config = tmp_path / "aliases.yaml"
        config.write_text("not_aliases: {}\n")
        with pytest.raises(NormalizationError):
            load_skill_aliases(config)
