"""Unit tests for transformer.validation.rules.cross_field_rules."""

from datetime import date

from transformer.models import OverallConfidence
from transformer.validation.rules.cross_field_rules import (
    ConfidenceFieldConsistencyRule,
    DateOrderRule,
)

from tests.unit.validation._builders import make_candidate, make_experience


def test_date_order_rule_passes_for_ordered_dates() -> None:
    candidate = make_candidate(
        experiences=[
            make_experience(
                start_date=date(2020, 1, 1), end_date=date(2021, 1, 1)
            )
        ]
    )
    assert DateOrderRule().check(candidate) == []


def test_date_order_rule_passes_for_current_role_no_end_date() -> None:
    candidate = make_candidate(
        experiences=[make_experience(start_date=date(2020, 1, 1), end_date=None)]
    )
    assert DateOrderRule().check(candidate) == []


def test_confidence_field_consistency_passes_for_known_field() -> None:
    candidate = make_candidate().model_copy(
        update={
            "confidence": OverallConfidence(score=0.8, fields={}),
        }
    )
    assert ConfidenceFieldConsistencyRule().check(candidate) == []


def test_confidence_field_consistency_flags_unknown_field_key() -> None:
    from transformer.models import DataSource, FieldConfidence

    candidate = make_candidate().model_copy(
        update={
            "confidence": OverallConfidence(
                score=0.8,
                fields={
                    "totally_bogus_field": FieldConfidence(
                        score=0.5, source=DataSource.ATS
                    )
                },
            ),
        }
    )
    issues = ConfidenceFieldConsistencyRule().check(candidate)
    assert len(issues) == 1
    assert issues[0].field == "totally_bogus_field"


def test_confidence_field_consistency_handles_dotted_field() -> None:
    from transformer.models import ContactInfo, DataSource, FieldConfidence

    candidate = make_candidate(contact=ContactInfo(email="a@b.com")).model_copy(
        update={
            "confidence": OverallConfidence(
                score=0.8,
                fields={
                    "contact.email": FieldConfidence(score=0.5, source=DataSource.ATS)
                },
            ),
        }
    )
    assert ConfidenceFieldConsistencyRule().check(candidate) == []
