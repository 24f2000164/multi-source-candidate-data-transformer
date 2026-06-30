"""Unit tests for transformer.validation.rules.duplicate_rules."""

from tests.unit.validation._builders import (
    make_candidate,
    make_education,
    make_experience,
)
from transformer.validation.rules.duplicate_rules import (
    DuplicateEducationRule,
    DuplicateExperienceRule,
)


def test_duplicate_experience_rule_passes_for_distinct_entries() -> None:
    candidate = make_candidate(
        experiences=[
            make_experience(company="Acme", title="Engineer"),
            make_experience(company="Globex", title="Manager"),
        ]
    )
    assert DuplicateExperienceRule().check(candidate) == []


def test_duplicate_experience_rule_flags_normalized_collision() -> None:
    candidate = make_candidate(
        experiences=[
            make_experience(company="Google", title="Engineer"),
            make_experience(company="  GOOGLE  ", title="engineer"),
        ]
    )
    issues = DuplicateExperienceRule().check(candidate)
    assert len(issues) == 1
    assert issues[0].field == "experiences[1]"


def test_duplicate_education_rule_flags_normalized_collision() -> None:
    candidate = make_candidate(
        education=[
            make_education(institution="MIT", degree="BSc"),
            make_education(institution="mit", degree="bsc"),
        ]
    )
    issues = DuplicateEducationRule().check(candidate)
    assert len(issues) == 1


def test_duplicate_rules_are_linear_in_entry_count() -> None:
    experiences = [
        make_experience(company=f"Company {i}", title="Engineer") for i in range(200)
    ]
    candidate = make_candidate(experiences=experiences)
    issues = DuplicateExperienceRule().check(candidate)
    assert issues == []
