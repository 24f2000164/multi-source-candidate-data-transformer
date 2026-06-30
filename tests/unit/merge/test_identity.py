"""Unit tests for transformer.merge.identity."""

from datetime import date

import pytest

from transformer.merge.identity import identity_key
from transformer.models import Education, WorkExperience


@pytest.mark.unit
class TestIdentityKey:
    def test_experience_identity_matches_case_insensitively(self) -> None:
        exp_a = WorkExperience(
            company="Acme Corp", title="Engineer", start_date=date(2020, 1, 1)
        )
        exp_b = WorkExperience(
            company="acme corp", title="ENGINEER", start_date=date(2020, 1, 1)
        )
        keys = ("company", "title", "start_date")
        assert identity_key(exp_a, keys) == identity_key(exp_b, keys)

    def test_experience_identity_differs_on_start_date(self) -> None:
        exp_a = WorkExperience(
            company="Acme", title="Engineer", start_date=date(2020, 1, 1)
        )
        exp_b = WorkExperience(
            company="Acme", title="Engineer", start_date=date(2021, 1, 1)
        )
        keys = ("company", "title", "start_date")
        assert identity_key(exp_a, keys) != identity_key(exp_b, keys)

    def test_education_identity(self) -> None:
        edu_a = Education(institution="MIT", degree="BSc")
        edu_b = Education(institution=" mit ", degree="bsc")
        keys = ("institution", "degree")
        assert identity_key(edu_a, keys) == identity_key(edu_b, keys)

    def test_none_attribute_normalizes_to_empty_string(self) -> None:
        edu = Education(institution="MIT", degree="BSc")
        key = identity_key(edu, ("institution", "field_of_study"))
        assert key == ("mit", "")
