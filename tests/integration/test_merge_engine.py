"""Integration tests for transformer.merge.merge_engine."""

from datetime import date

import pytest

from tests.unit.merge._builders import make_candidate
from transformer.merge.exceptions import MergeError
from transformer.merge.merge_engine import MergeEngine
from transformer.models import ContactInfo, DataSource, Education, WorkExperience


@pytest.fixture
def engine() -> MergeEngine:
    return MergeEngine()


@pytest.mark.integration
class TestMergeEngineTwoSource:
    def test_ats_wins_structured_fields_on_conflict(self, engine: MergeEngine) -> None:
        ats = make_candidate(DataSource.ATS, first_name="Jane", external_id="ATS-1")
        resume = make_candidate(DataSource.RESUME, first_name="Janet")
        golden, report = engine.merge([ats, resume])
        assert golden.first_name == "Jane"
        assert golden.external_id == "ATS-1"
        assert any(r.field == "first_name" for r in report.conflicts)

    def test_skills_union_across_sources(self, engine: MergeEngine) -> None:
        ats = make_candidate(DataSource.ATS, skills=["Python", "Go"])
        resume = make_candidate(DataSource.RESUME, skills=["python", "Rust"])
        golden, _ = engine.merge([ats, resume])
        assert golden.skills == ["python", "Rust", "Go"]  # RESUME priority for skills

    def test_experiences_merged_by_identity(self, engine: MergeEngine) -> None:
        shared = WorkExperience(
            company="Acme", title="Engineer", start_date=date(2020, 1, 1)
        )
        unique = WorkExperience(
            company="Globex", title="Manager", start_date=date(2021, 1, 1)
        )
        ats = make_candidate(DataSource.ATS, experiences=[shared])
        resume = make_candidate(DataSource.RESUME, experiences=[shared, unique])
        golden, _ = engine.merge([ats, resume])
        assert len(golden.experiences) == 2

    def test_both_missing_field_resolves_to_none_or_empty(
        self, engine: MergeEngine
    ) -> None:
        ats = make_candidate(DataSource.ATS)
        resume = make_candidate(DataSource.RESUME)
        golden, _ = engine.merge([ats, resume])
        assert golden.external_id is None
        assert golden.skills == []

    def test_both_identical_values_no_conflict(self, engine: MergeEngine) -> None:
        ats = make_candidate(DataSource.ATS, first_name="Jane")
        resume = make_candidate(DataSource.RESUME, first_name="Jane")
        golden, report = engine.merge([ats, resume])
        assert golden.first_name == "Jane"
        assert not any(r.field == "first_name" for r in report.conflicts)

    def test_empty_list_vs_missing_list(self, engine: MergeEngine) -> None:
        ats = make_candidate(DataSource.ATS, skills=[])
        resume = make_candidate(DataSource.RESUME, skills=["Python"])
        golden, _ = engine.merge([ats, resume])
        assert golden.skills == ["Python"]

    def test_phone_in_different_formats_treated_as_distinct_raw_values(
        self, engine: MergeEngine
    ) -> None:
        ats = make_candidate(DataSource.ATS, contact=ContactInfo(phone="+14155552671"))
        resume = make_candidate(
            DataSource.RESUME, contact=ContactInfo(phone="(415) 555-2671")
        )
        golden, report = engine.merge([ats, resume])
        assert golden.contact is not None
        assert golden.contact.phone == "+14155552671"  # ATS source priority wins
        assert any(r.field == "contact.phone" for r in report.conflicts)

    def test_education_merged_by_identity(self, engine: MergeEngine) -> None:
        shared = Education(institution="MIT", degree="BSc")
        ats = make_candidate(DataSource.ATS, education=[shared])
        resume = make_candidate(
            DataSource.RESUME, education=[Education(institution="mit", degree="bsc")]
        )
        golden, _ = engine.merge([ats, resume])
        assert len(golden.education) == 1


@pytest.mark.integration
class TestMergeEngineEdgeCases:
    def test_single_source_merge(self, engine: MergeEngine) -> None:
        ats = make_candidate(DataSource.ATS, first_name="Jane", skills=["Python"])
        golden, report = engine.merge([ats])
        assert golden.first_name == "Jane"
        assert golden.skills == ["Python"]
        assert report.conflicts == ()

    def test_more_than_two_sources(self, engine: MergeEngine) -> None:
        ats = make_candidate(DataSource.ATS, skills=["Python"])
        resume = make_candidate(DataSource.RESUME, skills=["Go"])
        third = make_candidate(DataSource.RESUME, skills=["Rust"])
        golden, _ = engine.merge([ats, resume, third])
        assert set(golden.skills) == {"Python", "Go", "Rust"}

    def test_empty_candidate_list_raises(self, engine: MergeEngine) -> None:
        with pytest.raises(MergeError):
            engine.merge([])

    def test_candidate_without_provenance_raises(self, engine: MergeEngine) -> None:
        from transformer.models import Candidate

        no_provenance = Candidate(first_name="Jane", last_name="Doe")
        with pytest.raises(MergeError):
            engine.merge([no_provenance])

    def test_provenance_preserved_for_winning_source(self, engine: MergeEngine) -> None:
        ats = make_candidate(DataSource.ATS, first_name="Jane")
        resume = make_candidate(DataSource.RESUME, first_name="Janet")
        golden, _ = engine.merge([ats, resume])
        assert golden.provenance["first_name"].source == DataSource.ATS

    def test_report_preserves_provenance_from_all_sources(
        self, engine: MergeEngine
    ) -> None:
        ats = make_candidate(DataSource.ATS, first_name="Jane")
        resume = make_candidate(DataSource.RESUME, first_name="Janet")
        _, report = engine.merge([ats, resume])
        record = next(r for r in report.fields if r.field == "first_name")
        assert DataSource.ATS in record.provenance
        assert DataSource.RESUME in record.provenance

    def test_merge_report_field_accessors(self, engine: MergeEngine) -> None:
        ats = make_candidate(DataSource.ATS, first_name="Jane", skills=["Python"])
        resume = make_candidate(DataSource.RESUME, first_name="Jane")
        _, report = engine.merge([ats, resume])
        assert "first_name" in report.merged_fields
        assert "skills" in report.merge_strategy
        assert report.merge_strategy["skills"] == "union"
        assert "first_name" in report.chosen_values
