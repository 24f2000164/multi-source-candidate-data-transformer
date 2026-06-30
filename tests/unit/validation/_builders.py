"""Shared builders for transformer.validation unit/integration tests."""

from datetime import date

from transformer.models import Candidate, ContactInfo, Education, WorkExperience


def make_candidate(
    *,
    first_name: str = "Jane",
    last_name: str = "Doe",
    external_id: str | None = None,
    contact: ContactInfo | None = None,
    experiences: list[WorkExperience] | None = None,
    education: list[Education] | None = None,
) -> Candidate:
    """Build a minimal valid ``Candidate`` for validation-rule tests."""
    return Candidate(
        first_name=first_name,
        last_name=last_name,
        external_id=external_id,
        contact=contact,
        experiences=experiences or [],
        education=education or [],
    )


def make_experience(
    *,
    company: str = "Acme",
    title: str = "Engineer",
    start_date: date = date(2020, 1, 1),
    end_date: date | None = None,
) -> WorkExperience:
    """Build a ``WorkExperience`` for validation-rule tests."""
    return WorkExperience(
        company=company, title=title, start_date=start_date, end_date=end_date
    )


def make_education(
    *, institution: str = "State University", degree: str = "BSc"
) -> Education:
    """Build an ``Education`` entry for validation-rule tests."""
    return Education(institution=institution, degree=degree)
