"""Unit tests for transformer.models.experience."""

from datetime import date, timedelta

from pydantic import ValidationError
import pytest

from transformer.models.experience import WorkExperience


def _today() -> date:
    return date.today()


def _past(days: int = 365) -> date:
    return _today() - timedelta(days=days)


def _future(days: int = 30) -> date:
    return _today() + timedelta(days=days)


@pytest.mark.unit
class TestWorkExperience:
    """Tests for WorkExperience."""

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_current_role(self) -> None:
        exp = WorkExperience(
            company="Acme Corp",
            title="Software Engineer",
            start_date=_past(500),
        )
        assert exp.end_date is None
        assert exp.skills == []

    def test_completed_role(self) -> None:
        exp = WorkExperience(
            company="Globex",
            title="Senior Engineer",
            start_date=_past(730),
            end_date=_past(100),
        )
        assert exp.end_date is not None

    def test_skills_deduped(self) -> None:
        exp = WorkExperience(
            company="Acme",
            title="Dev",
            start_date=_past(200),
            skills=["Python", "Python", "Go", "python"],
        )
        # "Python" and "python" are distinct strings — only exact duplicates removed
        assert exp.skills.count("Python") == 1

    def test_skills_blank_removed(self) -> None:
        exp = WorkExperience(
            company="Acme",
            title="Dev",
            start_date=_past(200),
            skills=["Python", "  ", "Go"],
        )
        assert "  " not in exp.skills
        assert "" not in exp.skills

    def test_description_stripped(self) -> None:
        exp = WorkExperience(
            company="Acme",
            title="Dev",
            start_date=_past(200),
            description="  Built things.  ",
        )
        assert exp.description == "Built things."

    def test_company_stripped(self) -> None:
        exp = WorkExperience(
            company="  Acme Corp  ",
            title="Dev",
            start_date=_past(200),
        )
        assert exp.company == "Acme Corp"

    def test_unicode_company(self) -> None:
        exp = WorkExperience(
            company="日本電気株式会社",
            title="Engineer",
            start_date=_past(300),
        )
        assert exp.company == "日本電気株式会社"

    # ------------------------------------------------------------------
    # Negative path
    # ------------------------------------------------------------------

    def test_future_start_date_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkExperience(
                company="Acme",
                title="Dev",
                start_date=_future(),
            )

    def test_end_before_start_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkExperience(
                company="Acme",
                title="Dev",
                start_date=_past(100),
                end_date=_past(200),
            )

    def test_blank_company_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkExperience(company="  ", title="Dev", start_date=_past(100))

    def test_blank_title_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkExperience(company="Acme", title="", start_date=_past(100))

    def test_blank_description_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkExperience(
                company="Acme",
                title="Dev",
                start_date=_past(100),
                description="   ",
            )

    def test_missing_company_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkExperience(title="Dev", start_date=_past(100))  # type: ignore[call-arg]

    def test_missing_start_date_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkExperience(company="Acme", title="Dev")  # type: ignore[call-arg]

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_same_start_and_end_date(self) -> None:
        d = _past(50)
        exp = WorkExperience(company="Acme", title="Dev", start_date=d, end_date=d)
        assert exp.start_date == exp.end_date

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            WorkExperience(
                company="Acme",
                title="Dev",
                start_date=_past(100),
                unexpected="x",
            )

    def test_frozen(self) -> None:
        exp = WorkExperience(company="Acme", title="Dev", start_date=_past(100))
        with pytest.raises(ValidationError):
            exp.company = "Other"  # type: ignore[misc]

    def test_large_skills_list(self) -> None:
        skills = [f"skill_{i}" for i in range(500)]
        exp = WorkExperience(
            company="Acme",
            title="Dev",
            start_date=_past(200),
            skills=skills,
        )
        assert len(exp.skills) == 500

    def test_skills_exceeding_max_raises(self) -> None:
        skills = [f"skill_{i}" for i in range(501)]
        with pytest.raises(ValidationError):
            WorkExperience(
                company="Acme",
                title="Dev",
                start_date=_past(200),
                skills=skills,
            )
