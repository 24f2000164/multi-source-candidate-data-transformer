"""Unit tests for transformer.merge.policy."""

from pathlib import Path

import pytest

from transformer.merge.exceptions import MergeError
from transformer.merge.policy import (
    DEFAULT_MERGE_POLICY_PATH,
    FieldRule,
    load_merge_policy,
)
from transformer.models import DataSource


@pytest.mark.unit
class TestLoadMergePolicy:
    def test_default_policy_loads(self) -> None:
        policy = load_merge_policy()
        assert policy.default_rule.strategy == "source_priority"
        assert policy.default_rule.priority == (DataSource.ATS, DataSource.RESUME)

    def test_field_override_used_when_present(self) -> None:
        policy = load_merge_policy()
        rule = policy.rule_for("skills")
        assert rule.strategy == "union"
        assert rule.identity_keys == ()

    def test_structured_list_field_has_identity_keys(self) -> None:
        policy = load_merge_policy()
        rule = policy.rule_for("experiences")
        assert rule.identity_keys == ("company", "title", "start_date")

    def test_unknown_field_falls_back_to_default(self) -> None:
        policy = load_merge_policy()
        rule = policy.rule_for("not_a_real_field")
        assert rule == policy.default_rule

    def test_default_path_exists(self) -> None:
        assert DEFAULT_MERGE_POLICY_PATH.exists()

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(MergeError):
            load_merge_policy(tmp_path / "does_not_exist.yaml")

    def test_invalid_default_strategy_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "policy.yaml"
        bad.write_text("default_strategy: nonsense\ndefault_priority: [ATS]\n")
        with pytest.raises(MergeError):
            load_merge_policy(bad)

    def test_invalid_priority_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "policy.yaml"
        bad.write_text(
            "default_strategy: source_priority\ndefault_priority: [NOT_A_SOURCE]\n"
        )
        with pytest.raises(MergeError):
            load_merge_policy(bad)

    def test_empty_priority_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "policy.yaml"
        bad.write_text("default_strategy: source_priority\ndefault_priority: []\n")
        with pytest.raises(MergeError):
            load_merge_policy(bad)

    def test_field_rule_with_unknown_strategy_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "policy.yaml"
        bad.write_text(
            "default_strategy: source_priority\n"
            "default_priority: [ATS]\n"
            "fields:\n"
            "  skills:\n"
            "    strategy: nonsense\n"
            "    priority: [ATS]\n"
        )
        with pytest.raises(MergeError):
            load_merge_policy(bad)


@pytest.mark.unit
class TestFieldRule:
    def test_default_identity_keys_is_empty_tuple(self) -> None:
        rule = FieldRule(strategy="source_priority", priority=(DataSource.ATS,))
        assert rule.identity_keys == ()
