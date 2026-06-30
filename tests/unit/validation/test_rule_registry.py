"""Unit tests for transformer.validation.rule_registry.RuleRegistry."""

import pytest

from transformer.validation.exceptions import DuplicateRuleNameError
from transformer.validation.rule import Severity
from transformer.validation.rule_registry import RuleRegistry


class _StubRule:
    def __init__(self, name: str) -> None:
        self.name = name
        self.severity = Severity.WARNING

    def check(self, candidate):
        return []


def test_get_rules_returns_rules_in_order() -> None:
    rule_a, rule_b = _StubRule("a"), _StubRule("b")
    registry = RuleRegistry([rule_a, rule_b])
    assert registry.get_rules() == (rule_a, rule_b)


def test_empty_registry_returns_empty_tuple() -> None:
    assert RuleRegistry([]).get_rules() == ()


def test_duplicate_rule_names_raise() -> None:
    with pytest.raises(DuplicateRuleNameError):
        RuleRegistry([_StubRule("email"), _StubRule("email")])
