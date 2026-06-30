"""Unit tests for transformer.parsers.resume.resume_mapper."""

import pytest

from transformer.models import DataSource
from transformer.parsers.exceptions import MappingError
from transformer.parsers.resume.extracted_data import (
    ExtractedResumeData,
    RawCertificationEntry,
    RawEducationEntry,
    RawExperienceEntry,
)
from transformer.parsers.resume.resume_mapper import ResumeMapper


class TestMapCandidateHappyPath:
    def test_maps_full_record(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="555-123-4567",
            linkedin_url="https://linkedin.com/in/janedoe",
            github_url="https://github.com/janedoe",
            skills=["Python", "SQL"],
            languages=["English"],
            experience_entries=[
                RawExperienceEntry(
                    company="Acme",
                    title="Engineer",
                    start_date="Jan 2020",
                    end_date="Dec 2022",
                )
            ],
            education_entries=[
                RawEducationEntry(institution="MIT", degree="BS Computer Science")
            ],
            certifications=[RawCertificationEntry(name="AWS Certified")],
        )
        candidate = ResumeMapper().map_candidate(data)
        assert candidate.first_name == "Jane"
        assert candidate.contact is not None
        assert candidate.contact.email == "jane@example.com"
        assert candidate.skills == ["Python", "SQL"]
        assert candidate.experiences[0].company == "Acme"
        assert candidate.education[0].institution == "MIT"
        assert candidate.certifications[0].name == "AWS Certified"
        assert candidate.provenance["first_name"].source == DataSource.RESUME

    def test_minimal_record_name_only(self) -> None:
        data = ExtractedResumeData(first_name="Jane", last_name="Doe")
        candidate = ResumeMapper().map_candidate(data)
        assert candidate.first_name == "Jane"
        assert candidate.contact is None


class TestMapCandidateNegativePath:
    def test_missing_name_raises_mapping_error(self) -> None:
        data = ExtractedResumeData(first_name=None, last_name=None)
        with pytest.raises(MappingError, match="Unable to detect candidate name"):
            ResumeMapper().map_candidate(data)

    def test_experience_missing_company_is_skipped_not_raised(self) -> None:
        """Per-entry graceful degradation: an invalid experience entry is
        dropped with a warning, the candidate still maps successfully."""
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            experience_entries=[
                RawExperienceEntry(company=None, title="Engineer", start_date="2020")
            ],
        )
        candidate = ResumeMapper().map_candidate(data)
        assert candidate.experiences == []

    def test_education_missing_degree_is_skipped_not_raised(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            education_entries=[RawEducationEntry(institution="MIT", degree=None)],
        )
        candidate = ResumeMapper().map_candidate(data)
        assert candidate.education == []

    def test_certification_missing_name_is_skipped_not_raised(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            certifications=[RawCertificationEntry(name=None, issuer="AWS")],
        )
        candidate = ResumeMapper().map_candidate(data)
        assert candidate.certifications == []

    def test_unparseable_required_start_date_is_skipped_not_raised(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            experience_entries=[
                RawExperienceEntry(
                    company="Acme", title="Engineer", start_date="not-a-date-xyz!!"
                )
            ],
        )
        candidate = ResumeMapper().map_candidate(data)
        assert candidate.experiences == []


class TestMapCandidatePerEntryGracefulDegradation:
    """One invalid entry must not discard otherwise-valid sibling entries."""

    def test_one_invalid_experience_does_not_drop_valid_siblings(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            experience_entries=[
                RawExperienceEntry(
                    company="Acme", title="Engineer", start_date="Jan 2020"
                ),
                RawExperienceEntry(title="Missing company and start_date"),
                RawExperienceEntry(
                    company="Globex", title="Lead", start_date="Jan 2018"
                ),
            ],
        )
        candidate = ResumeMapper().map_candidate(data)
        assert len(candidate.experiences) == 2
        assert [e.company for e in candidate.experiences] == ["Acme", "Globex"]

    def test_one_invalid_education_does_not_drop_valid_siblings(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            education_entries=[
                RawEducationEntry(institution="MIT", degree="BS"),
                RawEducationEntry(institution="No Degree University", degree=None),
            ],
        )
        candidate = ResumeMapper().map_candidate(data)
        assert len(candidate.education) == 1
        assert candidate.education[0].institution == "MIT"

    def test_all_invalid_entries_yields_empty_list_not_error(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            experience_entries=[
                RawExperienceEntry(title="No company or date"),
            ],
        )
        candidate = ResumeMapper().map_candidate(data)
        assert candidate.experiences == []
        # No provenance entry is recorded when every entry was dropped.
        assert "experiences" not in candidate.provenance


class TestOptionalDateParsing:
    def test_present_resolves_to_none_end_date(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            experience_entries=[
                RawExperienceEntry(
                    company="Acme",
                    title="Engineer",
                    start_date="2021",
                    end_date="Present",
                )
            ],
        )
        candidate = ResumeMapper().map_candidate(data)
        assert candidate.experiences[0].end_date is None
