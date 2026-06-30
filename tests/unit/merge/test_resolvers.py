"""Unit tests for transformer.merge.resolvers and field_resolver."""

from datetime import date

import pytest

from transformer.merge.exceptions import MergeError
from transformer.merge.field_resolver import FieldResolver
from transformer.merge.policy import FieldRule, MergePolicy
from transformer.merge.resolvers import (
    EducationResolver,
    ExperienceResolver,
    ListResolver,
    StringResolver,
)
from transformer.merge.strategies import SourceValue
from transformer.models import DataSource, Education, WorkExperience

_PRIORITY = (DataSource.ATS, DataSource.RESUME)


@pytest.mark.unit
class TestStringResolver:
    def test_resolves_via_source_priority(self) -> None:
        resolver = StringResolver()
        rule = FieldRule(strategy="source_priority", priority=_PRIORITY)
        result = resolver.resolve(
            "first_name",
            [
                SourceValue(DataSource.ATS, "Jane"),
                SourceValue(DataSource.RESUME, "Janet"),
            ],
            rule,
        )
        assert result.value == "Jane"
        assert result.conflict is True
        assert result.warnings != ()

    def test_invalid_strategy_for_scalar_raises(self) -> None:
        resolver = StringResolver()
        rule = FieldRule(strategy="union", priority=_PRIORITY)
        with pytest.raises(MergeError):
            resolver.resolve("first_name", [SourceValue(DataSource.ATS, "Jane")], rule)


@pytest.mark.unit
class TestListResolver:
    def test_unions_and_dedupes_case_insensitively(self) -> None:
        resolver = ListResolver()
        rule = FieldRule(strategy="union", priority=_PRIORITY)
        result = resolver.resolve(
            "skills",
            [
                SourceValue(DataSource.ATS, ["Python", "Go"]),
                SourceValue(DataSource.RESUME, ["python", "Rust"]),
            ],
            rule,
        )
        assert result.value == ["Python", "Go", "Rust"]

    def test_invalid_strategy_raises(self) -> None:
        resolver = ListResolver()
        rule = FieldRule(strategy="source_priority", priority=_PRIORITY)
        with pytest.raises(MergeError):
            resolver.resolve("skills", [SourceValue(DataSource.ATS, ["Python"])], rule)


@pytest.mark.unit
class TestExperienceResolver:
    def test_merges_by_identity_key(self) -> None:
        resolver = ExperienceResolver()
        rule = FieldRule(
            strategy="union",
            priority=_PRIORITY,
            identity_keys=("company", "title", "start_date"),
        )
        ats_exp = WorkExperience(
            company="Acme", title="Engineer", start_date=date(2020, 1, 1)
        )
        resume_exp_dup = WorkExperience(
            company="acme", title="ENGINEER", start_date=date(2020, 1, 1)
        )
        resume_exp_new = WorkExperience(
            company="Globex", title="Manager", start_date=date(2021, 1, 1)
        )
        result = resolver.resolve(
            "experiences",
            [
                SourceValue(DataSource.ATS, [ats_exp]),
                SourceValue(DataSource.RESUME, [resume_exp_dup, resume_exp_new]),
            ],
            rule,
        )
        assert len(result.value) == 2
        assert result.value[0] is ats_exp
        assert result.value[1] is resume_exp_new

    def test_missing_identity_keys_raises(self) -> None:
        resolver = ExperienceResolver()
        rule = FieldRule(strategy="union", priority=_PRIORITY)
        with pytest.raises(MergeError):
            resolver.resolve("experiences", [SourceValue(DataSource.ATS, [])], rule)


@pytest.mark.unit
class TestEducationResolver:
    def test_merges_by_institution_and_degree(self) -> None:
        resolver = EducationResolver()
        rule = FieldRule(
            strategy="union",
            priority=_PRIORITY,
            identity_keys=("institution", "degree"),
        )
        ats_edu = Education(institution="MIT", degree="BSc")
        resume_edu = Education(institution="mit", degree="bsc", field_of_study="CS")
        result = resolver.resolve(
            "education",
            [
                SourceValue(DataSource.ATS, [ats_edu]),
                SourceValue(DataSource.RESUME, [resume_edu]),
            ],
            rule,
        )
        assert len(result.value) == 1
        merged = result.value[0]
        # ATS wins on identity (higher priority source), but gap-fill pulls
        # field_of_study from RESUME since ATS left it blank — Issue 2 fix.
        assert merged.institution == "MIT"  # ATS casing preserved
        assert merged.degree == "BSc"       # ATS casing preserved
        assert merged.field_of_study == "CS"  # filled from RESUME


@pytest.mark.unit
class TestFieldResolverDispatch:
    def _policy(self) -> MergePolicy:
        return MergePolicy(
            default_rule=FieldRule(strategy="source_priority", priority=_PRIORITY),
            field_rules={
                "skills": FieldRule(strategy="union", priority=_PRIORITY),
                "experiences": FieldRule(
                    strategy="union",
                    priority=_PRIORITY,
                    identity_keys=("company", "title", "start_date"),
                ),
            },
        )

    def test_dispatches_scalar_to_string_resolver(self) -> None:
        resolver = FieldResolver(self._policy())
        result = resolver.resolve("first_name", [SourceValue(DataSource.ATS, "Jane")])
        assert result.value == "Jane"

    def test_dispatches_flat_list_to_list_resolver(self) -> None:
        resolver = FieldResolver(self._policy())
        result = resolver.resolve("skills", [SourceValue(DataSource.ATS, ["Python"])])
        assert result.value == ["Python"]

    def test_dispatches_structured_list_to_experience_resolver(self) -> None:
        resolver = FieldResolver(self._policy())
        exp = WorkExperience(company="Acme", title="Eng", start_date=date(2020, 1, 1))
        result = resolver.resolve("experiences", [SourceValue(DataSource.ATS, [exp])])
        assert result.value == [exp]
