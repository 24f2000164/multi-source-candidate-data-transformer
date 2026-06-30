"""Integration tests for transformer.normalizers.normalization_engine."""

from datetime import UTC, date, datetime

import pytest

from transformer.models import (
    Candidate,
    Certification,
    ContactInfo,
    DataSource,
    Education,
    FieldProvenance,
    WorkExperience,
)
from transformer.normalizers.normalization_engine import NormalizationEngine

_NOW = datetime.now(UTC)


def _provenance(field: str, raw: str) -> dict[str, FieldProvenance]:
    return {
        field: FieldProvenance(source=DataSource.ATS, raw_value=raw, extracted_at=_NOW)
    }


@pytest.fixture
def engine() -> NormalizationEngine:
    return NormalizationEngine(
        skill_alias_map={"js": "JavaScript", "javascript": "JavaScript"}
    )


@pytest.mark.integration
class TestNormalizationEngine:
    def test_normalizes_name_casing(self, engine: NormalizationEngine) -> None:
        candidate = Candidate(first_name="  john  ", last_name="SMITH")
        result = engine.normalize(candidate)
        assert result.first_name == "John"
        assert result.last_name == "Smith"

    def test_normalizes_contact_fields(self, engine: NormalizationEngine) -> None:
        candidate = Candidate(
            first_name="Jane",
            last_name="Doe",
            contact=ContactInfo(
                email="Jane.Doe@Example.COM ",
                phone="4155552671",
                location="  San   Francisco  ",
            ),
        )
        result = engine.normalize(candidate)
        assert result.contact is not None
        assert result.contact.email == "jane.doe@example.com"
        assert result.contact.phone == "+14155552671"
        assert result.contact.location == "San Francisco"

    def test_normalizes_and_dedupes_skills_with_aliases(
        self, engine: NormalizationEngine
    ) -> None:
        candidate = Candidate(
            first_name="Jane", last_name="Doe", skills=["js", "JavaScript", "Python "]
        )
        result = engine.normalize(candidate)
        assert result.skills == ["JavaScript", "Python"]

    def test_normalizes_nested_experience(self, engine: NormalizationEngine) -> None:
        candidate = Candidate(
            first_name="Jane",
            last_name="Doe",
            experiences=[
                WorkExperience(
                    company="  Acme  ",
                    title="  Engineer  ",
                    start_date=date(2020, 1, 1),
                    description="  Built things  ",
                    skills=["js"],
                )
            ],
        )
        result = engine.normalize(candidate)
        exp = result.experiences[0]
        assert exp.company == "Acme"
        assert exp.title == "Engineer"
        assert exp.description == "Built things"
        assert exp.skills == ["JavaScript"]

    def test_normalizes_education_and_certifications(
        self, engine: NormalizationEngine
    ) -> None:
        candidate = Candidate(
            first_name="Jane",
            last_name="Doe",
            education=[
                Education(
                    institution="  MIT  ", degree="  BSc  ", field_of_study="  CS  "
                )
            ],
            certifications=[Certification(name="  PMP  ", issuer="  PMI  ")],
        )
        result = engine.normalize(candidate)
        assert result.education[0].institution == "MIT"
        assert result.education[0].degree == "BSc"
        assert result.education[0].field_of_study == "CS"
        assert result.certifications[0].name == "PMP"
        assert result.certifications[0].issuer == "PMI"

    def test_preserves_id_provenance_confidence_schema_version(
        self, engine: NormalizationEngine
    ) -> None:
        candidate = Candidate(
            first_name="jane",
            last_name="doe",
            provenance=_provenance("first_name", "jane"),
            schema_version="1.0",
        )
        result = engine.normalize(candidate)
        assert result.id == candidate.id
        assert result.provenance == candidate.provenance
        assert result.schema_version == candidate.schema_version

    def test_idempotent(self, engine: NormalizationEngine) -> None:
        candidate = Candidate(
            first_name="  john  ",
            last_name="SMITH",
            skills=["js", "Python"],
            contact=ContactInfo(email="John@Example.COM", phone="4155552671"),
        )
        once = engine.normalize(candidate)
        twice = engine.normalize(once)
        assert once.first_name == twice.first_name
        assert once.skills == twice.skills
        assert once.contact == twice.contact

    def test_empty_candidate_has_no_optional_fields(
        self, engine: NormalizationEngine
    ) -> None:
        candidate = Candidate(first_name="Jane", last_name="Doe")
        result = engine.normalize(candidate)
        assert result.contact is None
        assert result.experiences == []
        assert result.education == []
        assert result.certifications == []
