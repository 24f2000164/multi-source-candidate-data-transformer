"""Unit tests for transformer.parsers.ats_mapper."""

from typing import Any

import pytest

from transformer.models import DataSource
from transformer.parsers.ats_mapper import ATSMapper
from transformer.parsers.exceptions import MappingError


@pytest.fixture
def mapper() -> ATSMapper:
    return ATSMapper()


def _minimal() -> dict[str, Any]:
    return {"first_name": "Alice", "last_name": "Smith"}


@pytest.mark.unit
class TestATSMapperHappyPath:
    def test_minimal_record_maps(self, mapper: ATSMapper) -> None:
        c = mapper.map_candidate(_minimal())
        assert c.first_name == "Alice"
        assert c.last_name == "Smith"
        assert c.external_id is None
        assert c.contact is None

    def test_full_record_maps(self, mapper: ATSMapper) -> None:
        data = {
            **_minimal(),
            "candidate_id": "ATS-1001",
            "email": "alice@example.com",
            "phone": "1234567890",
            "skills": ["Python", "FastAPI"],
            "experience": [
                {
                    "company": "Acme",
                    "title": "Engineer",
                    "start_date": "2022-01-01",
                    "end_date": "2023-01-01",
                }
            ],
            "education": [{"institution": "MIT", "degree": "BS"}],
            "certifications": [{"name": "AWS Certified"}],
            "languages": ["English"],
        }
        c = mapper.map_candidate(data)
        assert c.external_id == "ATS-1001"
        assert c.contact is not None
        assert c.contact.email == "alice@example.com"
        assert c.skills == ["Python", "FastAPI"]
        assert len(c.experiences) == 1
        assert c.experiences[0].company == "Acme"
        assert len(c.education) == 1
        assert len(c.certifications) == 1
        assert c.languages == ["English"]


@pytest.mark.unit
class TestATSMapperProvenance:
    def test_provenance_recorded_for_mapped_fields(self, mapper: ATSMapper) -> None:
        data = {**_minimal(), "email": "alice@example.com"}
        c = mapper.map_candidate(data)
        assert "first_name" in c.provenance
        assert "email" in c.provenance
        assert c.provenance["first_name"].source == DataSource.ATS
        assert c.provenance["first_name"].raw_value == "Alice"

    def test_no_provenance_for_absent_optional_fields(self, mapper: ATSMapper) -> None:
        c = mapper.map_candidate(_minimal())
        assert "email" not in c.provenance
        assert "external_id" not in c.provenance


@pytest.mark.unit
class TestATSMapperContact:
    def test_no_contact_fields_yields_none_contact(self, mapper: ATSMapper) -> None:
        c = mapper.map_candidate(_minimal())
        assert c.contact is None

    def test_invalid_email_raises_mapping_error(self, mapper: ATSMapper) -> None:
        data = {**_minimal(), "email": "not-an-email"}
        with pytest.raises(MappingError):
            mapper.map_candidate(data)

    def test_invalid_url_raises_mapping_error(self, mapper: ATSMapper) -> None:
        data = {**_minimal(), "linkedin_url": "not a url"}
        with pytest.raises(MappingError):
            mapper.map_candidate(data)


@pytest.mark.unit
class TestATSMapperRequiredNestedFields:
    """Invalid required nested fields must fail the entire candidate parse."""

    def test_experience_missing_company_raises(self, mapper: ATSMapper) -> None:
        data = {
            **_minimal(),
            "experience": [{"title": "Engineer", "start_date": "2022-01-01"}],
        }
        with pytest.raises(MappingError):
            mapper.map_candidate(data)

    def test_experience_missing_start_date_raises(self, mapper: ATSMapper) -> None:
        data = {
            **_minimal(),
            "experience": [{"company": "Acme", "title": "Engineer"}],
        }
        with pytest.raises(MappingError):
            mapper.map_candidate(data)

    def test_experience_invalid_date_format_raises(self, mapper: ATSMapper) -> None:
        data = {
            **_minimal(),
            "experience": [
                {
                    "company": "Acme",
                    "title": "Engineer",
                    "start_date": "not-a-date",
                }
            ],
        }
        with pytest.raises(MappingError):
            mapper.map_candidate(data)

    def test_education_missing_degree_raises(self, mapper: ATSMapper) -> None:
        data = {**_minimal(), "education": [{"institution": "MIT"}]}
        with pytest.raises(MappingError):
            mapper.map_candidate(data)

    def test_certification_missing_name_raises(self, mapper: ATSMapper) -> None:
        data = {**_minimal(), "certifications": [{"issuer": "AWS"}]}
        with pytest.raises(MappingError):
            mapper.map_candidate(data)

    def test_one_invalid_experience_fails_whole_record_deterministically(
        self, mapper: ATSMapper
    ) -> None:
        """Even with otherwise-valid entries, one invalid entry fails all."""
        data = {
            **_minimal(),
            "experience": [
                {
                    "company": "Acme",
                    "title": "Engineer",
                    "start_date": "2022-01-01",
                },
                {"title": "Missing company and start_date"},
            ],
        }
        with pytest.raises(MappingError):
            mapper.map_candidate(data)


@pytest.mark.unit
class TestATSMapperDuplicates:
    def test_duplicate_skills_deduplicated_by_model(self, mapper: ATSMapper) -> None:
        data = {**_minimal(), "skills": ["Python", "Python", "FastAPI"]}
        c = mapper.map_candidate(data)
        assert c.skills == ["Python", "FastAPI"]

    def test_duplicate_certifications_deduplicated_by_model(
        self, mapper: ATSMapper
    ) -> None:
        data = {
            **_minimal(),
            "certifications": [{"name": "AWS"}, {"name": "AWS"}],
        }
        c = mapper.map_candidate(data)
        assert len(c.certifications) == 1
