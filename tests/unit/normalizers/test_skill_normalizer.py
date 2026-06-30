"""Unit tests for transformer.normalizers.skill_normalizer."""

import pytest

from transformer.normalizers.skill_normalizer import normalize_skill, normalize_skills


@pytest.mark.unit
class TestNormalizeSkill:
    def test_cleans_whitespace(self) -> None:
        assert normalize_skill("  Python  ") == "Python"

    def test_alias_resolves_to_canonical(self) -> None:
        assert normalize_skill("js", {"js": "JavaScript"}) == "JavaScript"

    def test_alias_lookup_is_case_insensitive(self) -> None:
        assert normalize_skill("JS", {"js": "JavaScript"}) == "JavaScript"

    def test_no_alias_match_returns_cleaned_original(self) -> None:
        assert normalize_skill("Rust", {"js": "JavaScript"}) == "Rust"

    def test_no_alias_map_returns_cleaned_original(self) -> None:
        assert normalize_skill("python") == "python"


@pytest.mark.unit
class TestNormalizeSkills:
    def test_deduplicates_case_insensitively(self) -> None:
        result = normalize_skills(["Python", "python", "PYTHON"])
        assert result == ["Python"]

    def test_preserves_first_occurrence_order(self) -> None:
        result = normalize_skills(["Go", "Python", "go"])
        assert result == ["Go", "Python"]

    def test_alias_dedup_merges_variants(self) -> None:
        alias_map = {"js": "JavaScript", "javascript": "JavaScript"}
        result = normalize_skills(["js", "JavaScript", "Python"], alias_map)
        assert result == ["JavaScript", "Python"]

    def test_blank_skills_dropped(self) -> None:
        assert normalize_skills(["Python", "   ", ""]) == ["Python"]

    def test_empty_list(self) -> None:
        assert normalize_skills([]) == []
