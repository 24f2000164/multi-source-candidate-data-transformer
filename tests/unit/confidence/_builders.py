"""Shared builders for transformer.confidence unit/integration tests."""

from datetime import date

from transformer.models import Candidate, ContactInfo, WorkExperience


def make_candidate(
    *,
    first_name: str = "Jane",
    last_name: str = "Doe",
    contact: ContactInfo | None = None,
    skills: list[str] | None = None,
    experiences: list[WorkExperience] | None = None,
) -> Candidate:
    """Build a minimal ``Candidate`` for confidence-engine tests."""
    return Candidate(
        first_name=first_name,
        last_name=last_name,
        contact=contact,
        skills=skills or [],
        experiences=experiences or [],
    )


def make_experience(
    *, company: str = "Acme", title: str = "Engineer"
) -> WorkExperience:
    """Build a minimal ``WorkExperience`` for confidence-engine tests."""
    return WorkExperience(
        company=company, title=title, start_date=date(2020, 1, 1)
    )
