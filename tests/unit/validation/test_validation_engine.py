"""Unit tests for transformer.validation.validation_engine.ValidationEngine."""

from transformer.validation.rule import Severity, ValidationIssue
from transformer.validation.rule_registry import RuleRegistry
from transformer.validation.validation_engine import ValidationEngine

from tests.unit.validation._builders import make_candidate


class _PassingRule:
    name = "passing"
    severity = Severity.INFO

    def check(self, candidate):
        return []


class _FailingRule:
    name = "failing"
    severity = Severity.ERROR

    def check(self, candidate):
        return [
            ValidationIssue(
                rule_name=self.name,
                severity=self.severity,
                message="always fails",
            )
        ]


def test_engine_runs_all_rules_and_tracks_timing() -> None:
    registry = RuleRegistry([_PassingRule(), _FailingRule()])
    engine = ValidationEngine(registry, config_version="1.0")
    report = engine.run(make_candidate())

    assert report.rules_executed == ("passing", "failing")
    assert report.rules_failed == ("failing",)
    assert len(report.issues) == 1
    assert report.is_valid is False
    assert report.execution_time_ms >= 0.0
    assert report.config_version == "1.0"


def test_engine_with_empty_registry_produces_valid_report() -> None:
    engine = ValidationEngine(RuleRegistry([]))
    report = engine.run(make_candidate())
    assert report.is_valid is True
    assert report.issues == ()
    assert "PASS" in report.summary


def test_engine_all_passing_rules_is_valid() -> None:
    registry = RuleRegistry([_PassingRule()])
    engine = ValidationEngine(registry)
    report = engine.run(make_candidate())
    assert report.is_valid is True
