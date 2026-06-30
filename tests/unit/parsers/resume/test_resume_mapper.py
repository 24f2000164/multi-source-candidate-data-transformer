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

    def test_experience_missing_company_raises_mapping_error(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            experience_entries=[
                RawExperienceEntry(company=None, title="Engineer", start_date="2020")
            ],
        )
        with pytest.raises(MappingError):
            ResumeMapper().map_candidate(data)

    def test_education_missing_degree_raises_mapping_error(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            education_entries=[RawEducationEntry(institution="MIT", degree=None)],
        )
        with pytest.raises(MappingError):
            ResumeMapper().map_candidate(data)

    def test_certification_missing_name_raises_mapping_error(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            certifications=[RawCertificationEntry(name=None, issuer="AWS")],
        )
        with pytest.raises(MappingError):
            ResumeMapper().map_candidate(data)

    def test_unparseable_required_start_date_raises_mapping_error(self) -> None:
        data = ExtractedResumeData(
            first_name="Jane",
            last_name="Doe",
            experience_entries=[
                RawExperienceEntry(
                    company="Acme", title="Engineer", start_date="not-a-date-xyz!!"
                )
            ],
        )
        with pytest.raises(MappingError):
            ResumeMapper().map_candidate(data)


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
