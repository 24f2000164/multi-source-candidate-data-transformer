"""Sprint 09/10 integration coverage for application and pipeline wiring."""

from datetime import date
from pathlib import Path

import pytest

from transformer.cli.app import build_application_service
from transformer.models import Candidate, WorkExperience
from transformer.parsers.exceptions import ParserError
from transformer.projection.exceptions import UnknownProjectionTypeError
from transformer.validation.report import ValidationReport

_ROOT = Path(__file__).resolve().parents[2]
_SAMPLES = _ROOT / "samples"
_VALID_REGRESSION_RESUMES = (
    "company_location.docx",
    "date_formats.docx",
    "graceful_degradation.docx",
    "No_Experience.pdf",
    "no_skills.pdf",
    "sahil_resume.pdf",
    "same_line_resume.docx",
    "Standard_resume.docx",
    "Two_Page_resume.pdf",
)
_INVALID_REGRESSION_RESUMES = (
    "canva_resume.pdf",
    "degree_alias.docx",
    "Europass.pdf",
    "gpa_resume.docx",
    "school_denylist.docx",
    "sherlock_resume.pdf",
)


def _write_candidate(path: Path, candidate: Candidate) -> Path:
    path.write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
    return path


def test_ats_only_pipeline() -> None:
    result = build_application_service().parse(_SAMPLES / "inputs" / "my_test.json")

    assert result.candidate is not None
    assert result.projection is not None
    assert "ats_parser" in result.reports
    assert "confidence" in result.reports
    assert "validation" in result.reports


def test_resume_only_pipeline() -> None:
    result = build_application_service().parse(
        _SAMPLES / "resumes" / "Standard_resume.docx"
    )

    assert result.candidate is not None
    assert "resume_parser" in result.reports
    assert "validation" in result.reports


def test_ats_and_resume_full_transform() -> None:
    result = build_application_service().transform(
        _SAMPLES / "inputs" / "my_test.json",
        _SAMPLES / "resumes" / "sahil_resume.pdf",
    )

    assert result.candidate is not None
    assert result.projection is not None
    assert "merge" in result.reports
    assert list(result.reports).count("ats_parser") == 1
    assert list(result.reports).count("resume_parser") == 1


def test_invalid_ats_stops_pipeline(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ParserError):
        build_application_service().parse(invalid)


def test_invalid_resume_stops_pipeline(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.pdf"
    invalid.write_bytes(b"not a pdf")

    with pytest.raises(ParserError):
        build_application_service().parse(invalid)


def test_validation_failure_returns_unsuccessful_result(tmp_path: Path) -> None:
    candidate = Candidate(first_name="Jane", last_name="Doe", external_id="invalid id!")
    path = _write_candidate(tmp_path / "candidate.json", candidate)

    result = build_application_service().validate(path)

    assert result.success is False
    assert result.exit_code == 1
    validation_report = result.reports["validation"]
    assert isinstance(validation_report, ValidationReport)
    assert validation_report.is_valid is False


def test_unknown_projection_is_fatal(tmp_path: Path) -> None:
    path = _write_candidate(
        tmp_path / "candidate.json",
        Candidate(first_name="Jane", last_name="Doe"),
    )

    with pytest.raises(UnknownProjectionTypeError):
        build_application_service().project(path, "unknown")


def test_large_candidate_projects_without_data_loss(tmp_path: Path) -> None:
    candidate = Candidate(
        first_name="Large",
        last_name="Candidate",
        skills=[f"skill-{index}" for index in range(200)],
        experiences=[
            WorkExperience(
                company=f"Company {index}",
                title="Engineer",
                start_date=date(2020, 1, 1),
            )
            for index in range(50)
        ],
    )
    path = _write_candidate(tmp_path / "large.json", candidate)

    result = build_application_service().project(path, "canonical")

    assert result.projection is not None
    assert len(result.projection["skills"]) == 200
    assert len(result.projection["experiences"]) == 50


@pytest.mark.parametrize(
    "resume_name",
    _VALID_REGRESSION_RESUMES,
)
def test_valid_regression_resumes_complete(resume_name: str) -> None:
    result = build_application_service().parse(_SAMPLES / "resumes" / resume_name)

    assert result.candidate is not None
    assert result.candidate.first_name
    assert result.candidate.last_name


@pytest.mark.parametrize("resume_name", _INVALID_REGRESSION_RESUMES)
def test_invalid_regression_resumes_fail_gracefully(resume_name: str) -> None:
    with pytest.raises(ParserError, match=r"\S+"):
        build_application_service().parse(_SAMPLES / "resumes" / resume_name)
