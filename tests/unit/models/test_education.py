"""Unit tests for transformer.models.education."""

from datetime import date, timedelta

from pydantic import ValidationError
import pytest

from transformer.models.education import Certification, Education


def _past(days: int = 365) -> date:
    return date.today() - timedelta(days=days)


def _future(days: int = 365) -> date:
    return date.today() + timedelta(days=days)


@pytest.mark.unit
class TestEducation:
    """Tests for Education."""

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_required_fields_only(self) -> None:
        edu = Education(institution="MIT", degree="B.Sc. Computer Science")
        assert edu.institution == "MIT"
        assert edu.degree == "B.Sc. Computer Science"
        assert edu.gpa is None
        assert edu.start_date is None
        assert edu.end_date is None

    def test_full_fields(self) -> None:
        edu = Education(
            institution="Stanford University",
            degree="M.Sc. AI",
            field_of_study="Artificial Intelligence",
            start_date=_past(730),
            end_date=_past(100),
            gpa=3.9,
        )
        assert edu.gpa == 3.9

    def test_gpa_boundary_min(self) -> None:
        edu = Education(institution="MIT", degree="B.Sc.", gpa=0.0)
        assert edu.gpa == 0.0

    def test_gpa_boundary_max(self) -> None:
        edu = Education(institution="MIT", degree="B.Sc.", gpa=4.0)
        assert edu.gpa == 4.0

    def test_institution_stripped(self) -> None:
        edu = Education(institution="  Harvard  ", degree="B.A.")
        assert edu.institution == "Harvard"

    def test_ongoing_study_no_end_date(self) -> None:
        edu = Education(
            institution="Oxford",
            degree="D.Phil.",
            start_date=_past(400),
            end_date=None,
        )
        assert edu.end_date is None

    def test_unicode_institution(self) -> None:
        edu = Education(institution="Université de Paris", degree="Licence")
        assert edu.institution == "Université de Paris"

    # ------------------------------------------------------------------
    # Negative path
    # ------------------------------------------------------------------

    def test_end_before_start_raises(self) -> None:
        with pytest.raises(ValidationError):
            Education(
                institution="MIT",
                degree="B.Sc.",
                start_date=_past(100),
                end_date=_past(200),
            )

    def test_gpa_above_max_raises(self) -> None:
        with pytest.raises(ValidationError):
            Education(institution="MIT", degree="B.Sc.", gpa=4.1)

    def test_gpa_below_min_raises(self) -> None:
        with pytest.raises(ValidationError):
            Education(institution="MIT", degree="B.Sc.", gpa=-0.1)

    def test_blank_institution_raises(self) -> None:
        with pytest.raises(ValidationError):
            Education(institution="   ", degree="B.Sc.")

    def test_blank_degree_raises(self) -> None:
        with pytest.raises(ValidationError):
            Education(institution="MIT", degree="")

    def test_blank_field_of_study_raises(self) -> None:
        with pytest.raises(ValidationError):
            Education(institution="MIT", degree="B.Sc.", field_of_study="  ")

    def test_missing_institution_raises(self) -> None:
        with pytest.raises(ValidationError):
            Education(degree="B.Sc.")  # type: ignore[call-arg]

    def test_missing_degree_raises(self) -> None:
        with pytest.raises(ValidationError):
            Education(institution="MIT")  # type: ignore[call-arg]

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_same_start_and_end_date(self) -> None:
        d = _past(10)
        edu = Education(institution="MIT", degree="B.Sc.", start_date=d, end_date=d)
        assert edu.start_date == edu.end_date

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Education(institution="MIT", degree="B.Sc.", unexpected="x")

    def test_frozen(self) -> None:
        edu = Education(institution="MIT", degree="B.Sc.")
        with pytest.raises(ValidationError):
            edu.institution = "Harvard"  # type: ignore[misc]


@pytest.mark.unit
class TestCertification:
    """Tests for Certification."""

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_name_only(self) -> None:
        cert = Certification(name="AWS Solutions Architect")
        assert cert.name == "AWS Solutions Architect"
        assert cert.issuer is None
        assert cert.issued_date is None
        assert cert.expiry_date is None

    def test_full_fields(self) -> None:
        cert = Certification(
            name="CKA",
            issuer="CNCF",
            issued_date=_past(180),
            expiry_date=_future(550),
        )
        assert cert.issuer == "CNCF"

    def test_name_stripped(self) -> None:
        cert = Certification(name="  PMP  ")
        assert cert.name == "PMP"

    def test_perpetual_cert_no_expiry(self) -> None:
        cert = Certification(name="Oracle DBA", issued_date=_past(365))
        assert cert.expiry_date is None

    def test_unicode_name(self) -> None:
        cert = Certification(name="情報処理技術者試験")
        assert cert.name == "情報処理技術者試験"

    # ------------------------------------------------------------------
    # Negative path
    # ------------------------------------------------------------------

    def test_expiry_before_issued_raises(self) -> None:
        with pytest.raises(ValidationError):
            Certification(
                name="AWS",
                issued_date=_past(100),
                expiry_date=_past(200),
            )

    def test_blank_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            Certification(name="")

    def test_blank_issuer_raises(self) -> None:
        with pytest.raises(ValidationError):
            Certification(name="AWS", issuer="  ")

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            Certification()  # type: ignore[call-arg]

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_same_issued_and_expiry_date(self) -> None:
        d = _past(10)
        cert = Certification(name="AWS", issued_date=d, expiry_date=d)
        assert cert.issued_date == cert.expiry_date

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Certification(name="AWS", unexpected="x")

    def test_frozen(self) -> None:
        cert = Certification(name="AWS")
        with pytest.raises(ValidationError):
            cert.name = "GCP"  # type: ignore[misc]
