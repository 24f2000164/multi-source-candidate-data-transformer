"""Unit tests for ``AssignmentProjection``."""

from pathlib import Path

import pytest

from transformer.projection.assignment_projection import AssignmentProjection
from transformer.projection.exceptions import ProjectionError
from tests.unit.projection._builders import full_candidate, make_candidate


def _write_rules(tmp_path: Path, body: str) -> Path:
    rules_path = tmp_path / "projection_rules.yaml"
    rules_path.write_text(f'version: "1.0"\n{body}', encoding="utf-8")
    return rules_path


class TestAssignmentProjection:
    def test_uses_repo_default_rules_file(self) -> None:
        candidate = full_candidate()
        result = AssignmentProjection().project(candidate)

        assert result["firstName"] == "Jane"
        assert result["lastName"] == "Doe"
        assert result["email"] == "jane.doe@example.com"

    def test_includes_only_configured_fields(self, tmp_path: Path) -> None:
        rules_path = _write_rules(
            tmp_path,
            "fields:\n"
            "  first_name:\n"
            "    output: firstName\n",
        )
        candidate = full_candidate()
        result = AssignmentProjection(rules_path=rules_path).project(candidate)

        assert result == {"firstName": "Jane"}

    def test_renames_fields(self, tmp_path: Path) -> None:
        rules_path = _write_rules(
            tmp_path,
            "fields:\n"
            "  last_name:\n"
            "    output: surname\n",
        )
        candidate = make_candidate(last_name="Smith")
        result = AssignmentProjection(rules_path=rules_path).project(candidate)

        assert result == {"surname": "Smith"}

    def test_nested_path_resolution(self, tmp_path: Path) -> None:
        rules_path = _write_rules(
            tmp_path,
            "fields:\n"
            "  contact.email:\n"
            "    output: email\n",
        )
        candidate = full_candidate()
        result = AssignmentProjection(rules_path=rules_path).project(candidate)

        assert result == {"email": "jane.doe@example.com"}

    def test_missing_optional_field_is_omitted(self, tmp_path: Path) -> None:
        rules_path = _write_rules(
            tmp_path,
            "fields:\n"
            "  contact.email:\n"
            "    output: email\n",
        )
        candidate = make_candidate(contact=None)
        result = AssignmentProjection(rules_path=rules_path).project(candidate)

        assert result == {}

    def test_missing_fields_mapping_raises(self, tmp_path: Path) -> None:
        rules_path = _write_rules(tmp_path, "options:\n  foo: bar\n")

        with pytest.raises(ProjectionError):
            AssignmentProjection(rules_path=rules_path)

    def test_rule_without_output_key_raises(self, tmp_path: Path) -> None:
        rules_path = _write_rules(
            tmp_path,
            "fields:\n"
            "  first_name:\n"
            "    something_else: x\n",
        )

        with pytest.raises(ProjectionError):
            AssignmentProjection(rules_path=rules_path)

    def test_does_not_mutate_candidate(self, tmp_path: Path) -> None:
        rules_path = _write_rules(
            tmp_path,
            "fields:\n"
            "  first_name:\n"
            "    output: firstName\n",
        )
        candidate = full_candidate()
        before = candidate.model_dump(mode="json")
        AssignmentProjection(rules_path=rules_path).project(candidate)

        assert candidate.model_dump(mode="json") == before
