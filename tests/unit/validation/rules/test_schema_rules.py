"""Unit tests for transformer.validation.rules.schema_rules."""

from tests.unit.validation._builders import make_candidate
from transformer.models import OverallConfidence
from transformer.validation.rule import Severity
from transformer.validation.rules.schema_rules import (
    ConfidenceValueRule,
    IdRule,
    RequiredFieldsRule,
    SchemaVersionRule,
    StringLengthRule,
    UnicodeConfusableRule,
)


def test_required_fields_pass_for_valid_candidate() -> None:
    candidate = make_candidate()
    assert RequiredFieldsRule().check(candidate) == []


def test_schema_version_pass_for_known_version() -> None:
    candidate = make_candidate()
    assert SchemaVersionRule().check(candidate) == []


def test_schema_version_fails_for_unknown_version() -> None:
    candidate = make_candidate().model_copy(update={"schema_version": "9.9"})
    issues = SchemaVersionRule().check(candidate)
    assert len(issues) == 1
    assert issues[0].severity == Severity.ERROR
    assert issues[0].field == "schema_version"


def test_confidence_values_pass_when_absent() -> None:
    candidate = make_candidate()
    assert ConfidenceValueRule().check(candidate) == []


def test_confidence_values_pass_for_valid_score() -> None:
    candidate = make_candidate().model_copy(
        update={"confidence": OverallConfidence(score=0.8, fields={})}
    )
    assert ConfidenceValueRule().check(candidate) == []


def test_id_rule_passes_for_valid_uuid() -> None:
    candidate = make_candidate()
    assert IdRule().check(candidate) == []


def test_string_length_rule_passes_for_short_names() -> None:
    candidate = make_candidate()
    assert StringLengthRule(max_length=10_000).check(candidate) == []


def test_string_length_rule_flags_overflow() -> None:
    candidate = make_candidate(first_name="A" * 50)
    issues = StringLengthRule(max_length=10).check(candidate)
    assert len(issues) == 1
    assert issues[0].field == "first_name"


def test_unicode_confusable_rule_passes_for_plain_latin_name() -> None:
    candidate = make_candidate(first_name="Maria", last_name="Garcia")
    assert UnicodeConfusableRule().check(candidate) == []


def test_unicode_confusable_rule_flags_mixed_script_name() -> None:
   # 'а' (U+0430 CYRILLIC SMALL LETTER A) mixed with Latin letters.  # noqa: RUF003
    spoofed_name = "M\u0430ria"
    candidate = make_candidate(first_name=spoofed_name)
    issues = UnicodeConfusableRule().check(candidate)
    assert len(issues) == 1
    assert issues[0].severity == Severity.WARNING
