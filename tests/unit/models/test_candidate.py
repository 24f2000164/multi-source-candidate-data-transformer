"""Unit tests for transformer.models.candidate."""

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from pydantic import ValidationError
import pytest

from transformer.models.candidate import Candidate
from transformer.models.confidence import FieldConfidence, OverallConfidence
from transformer.models.contact import ContactInfo
from transformer.models.education import Certification, Education
from transformer.models.enums import DataSource
from transformer.models.experience import WorkExperience
from transformer.models.provenance import FieldProvenance


def _past(days: int = 365) -> date:
    return date.today() - timedelta(days=days)


def _make_candidate(**overrides: object) -> Candidate:
    defaults: dict[str, object] = {
        "first_name": "Alice",
        "last_name": "Smith",
    }
    defaults.update(overrides)
    return Candidate(**defaults)  # type: ignore[arg-type]


@pytest.mark.unit
class TestCandidateMinimal:
    """Tests for Candidate with minimal required fields."""

    def test_minimal_creation(self) -> None:
        c = _make_candidate()
        assert c.first_name == "Alice"
        assert c.last_name == "Smith"

    def test_auto_generated_uuid(self) -> None:
        c = _make_candidate()
        assert isinstance(c.id, UUID)

    def test_two_candidates_have_different_ids(self) -> None:
        c1 = _make_candidate()
        c2 = _make_candidate()
        assert c1.id != c2.id

    def test_custom_id(self) -> None:
        uid = uuid4()
        c = _make_candidate(id=uid)
        assert c.id == uid

    def test_default_schema_version(self) -> None:
        c = _make_candidate()
        assert c.schema_version == "1.0"

    def test_default_empty_collections(self) -> None:
        c = _make_candidate()
        assert c.experiences == []
        assert c.education == []
        assert c.skills == []
        assert c.certifications == []
        assert c.languages == []
        assert c.provenance == {}

    def test_default_none_optionals(self) -> None:
        c = _make_candidate()
        assert c.contact is None
        assert c.confidence is None


@pytest.mark.unit
class TestCandidateNameValidation:
    """Name field validation tests."""

    def test_first_name_stripped(self) -> None:
        c = _make_candidate(first_name="  Alice  ")
        assert c.first_name == "Alice"

    def test_last_name_stripped(self) -> None:
        c = _make_candidate(last_name="  Smith  ")
        assert c.last_name == "Smith"

    def test_blank_first_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(first_name="   ")

    def test_empty_first_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(first_name="")

    def test_blank_last_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(last_name="")

    def test_unicode_first_name(self) -> None:
        c = _make_candidate(first_name="José")
        assert c.first_name == "José"

    def test_unicode_last_name(self) -> None:
        c = _make_candidate(last_name="张伟")
        assert c.last_name == "张伟"

    def test_missing_first_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            Candidate(last_name="Smith")  # type: ignore[call-arg]

    def test_missing_last_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            Candidate(first_name="Alice")  # type: ignore[call-arg]


@pytest.mark.unit
class TestCandidateSkills:
    """Skills deduplication and validation tests."""

    def test_duplicate_skills_deduped(self) -> None:
        c = _make_candidate(skills=["Python", "Go", "Python"])
        assert c.skills.count("Python") == 1

    def test_blank_skills_removed(self) -> None:
        c = _make_candidate(skills=["Python", "  ", "Go", ""])
        assert "  " not in c.skills
        assert "" not in c.skills

    def test_skill_order_preserved(self) -> None:
        c = _make_candidate(skills=["Go", "Rust", "Python"])
        assert c.skills == ["Go", "Rust", "Python"]

    def test_skills_stripped(self) -> None:
        c = _make_candidate(skills=["  Python  ", "  Go  "])
        assert "Python" in c.skills
        assert "Go" in c.skills

    def test_large_skills_list(self) -> None:
        skills = [f"skill_{i}" for i in range(500)]
        c = _make_candidate(skills=skills)
        assert len(c.skills) == 500

    def test_skills_exceeding_max_raises(self) -> None:
        skills = [f"skill_{i}" for i in range(501)]
        with pytest.raises(ValidationError):
            _make_candidate(skills=skills)


@pytest.mark.unit
class TestCandidateLanguages:
    """Languages deduplication and validation tests."""

    def test_duplicate_languages_deduped(self) -> None:
        c = _make_candidate(languages=["English", "French", "English"])
        assert c.languages.count("English") == 1

    def test_blank_languages_removed(self) -> None:
        c = _make_candidate(languages=["English", "", "French"])
        assert "" not in c.languages


@pytest.mark.unit
class TestCandidateCertifications:
    """Certification deduplication tests."""

    def test_duplicate_certifications_deduped(self) -> None:
        certs = [
            {"name": "AWS SAA"},
            {"name": "AWS SAA"},
            {"name": "CKA"},
        ]
        c = _make_candidate(certifications=certs)
        names = [cert.name for cert in c.certifications]
        assert names.count("AWS SAA") == 1

    def test_case_insensitive_cert_dedup(self) -> None:
        certs = [
            {"name": "AWS SAA"},
            {"name": "aws saa"},
        ]
        c = _make_candidate(certifications=certs)
        # Second entry is a duplicate (case-insensitive key); only first kept
        assert len(c.certifications) == 1

    def test_cert_order_preserved(self) -> None:
        certs = [{"name": "CKA"}, {"name": "AWS SAA"}, {"name": "GCP ACE"}]
        c = _make_candidate(certifications=certs)
        assert [cert.name for cert in c.certifications] == ["CKA", "AWS SAA", "GCP ACE"]


@pytest.mark.unit
class TestCandidateFull:
    """Tests for a fully-populated Candidate."""

    def test_full_candidate(self) -> None:
        c = Candidate(
            first_name="Alice",
            last_name="Smith",
            contact=ContactInfo(email="alice@example.com"),
            experiences=[
                WorkExperience(
                    company="Acme",
                    title="Engineer",
                    start_date=_past(730),
                    end_date=_past(100),
                )
            ],
            education=[Education(institution="MIT", degree="B.Sc.")],
            skills=["Python", "Go"],
            certifications=[Certification(name="AWS SAA")],
            languages=["English", "French"],
            confidence=OverallConfidence(
                score=0.9,
                fields={
                    "first_name": FieldConfidence(score=1.0, source=DataSource.ATS)
                },
            ),
            provenance={
                "first_name": FieldProvenance(
                    source=DataSource.ATS,
                    raw_value="Alice",
                    extracted_at=datetime(2024, 1, 1, tzinfo=UTC),
                )
            },
            schema_version="1.0",
        )
        assert c.first_name == "Alice"
        assert len(c.experiences) == 1
        assert c.confidence is not None
        assert c.confidence.score == 0.9

    def test_serialises_to_dict(self) -> None:
        c = _make_candidate(skills=["Python"])
        d = c.model_dump()
        assert d["first_name"] == "Alice"
        assert d["skills"] == ["Python"]

    def test_serialises_to_json(self) -> None:
        c = _make_candidate()
        j = c.model_dump_json()
        assert "Alice" in j


@pytest.mark.unit
class TestCandidateSchemaVersion:
    """Schema version field tests."""

    def test_custom_schema_version(self) -> None:
        c = _make_candidate(schema_version="2.0")
        assert c.schema_version == "2.0"

    def test_blank_schema_version_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(schema_version="   ")


@pytest.mark.unit
class TestCandidateImmutability:
    """Immutability tests for the Candidate root model."""

    def test_frozen(self) -> None:
        c = _make_candidate()
        with pytest.raises(ValidationError):
            c.first_name = "Bob"  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(unexpected_field="x")
