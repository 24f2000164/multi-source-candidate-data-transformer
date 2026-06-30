"""Shared builders for transformer.projection unit/integration tests."""

from datetime import date
from typing import Any

from transformer.models import Candidate, ContactInfo, Education, WorkExperience


def make_candidate(
    *,
    first_name: str = "Jane",
    last_name: str = "Doe",
    external_id: str | None = "ext-123",
    contact: ContactInfo | None = None,
    skills: list[str] | None = None,
    languages: list[str] | None = None,
    experiences: list[WorkExperience] | None = None,
    education: list[Education] | None = None,
    **extra: Any,
) -> Candidate:
    """Build a ``Candidate`` with sensible defaults for projection tests."""
    kwargs: dict[str, Any] = {"first_name": first_name, "last_name": last_name}
    if external_id is not None:
        kwargs["external_id"] = external_id
    if contact is not None:
        kwargs["contact"] = contact
    if skills is not None:
        kwargs["skills"] = skills
    if languages is not None:
        kwargs["languages"] = languages
    if experiences is not None:
        kwargs["experiences"] = experiences
    if education is not None:
        kwargs["education"] = education
    kwargs.update(extra)
    return Candidate(**kwargs)


def full_candidate() -> Candidate:
    """Build a ``Candidate`` with every field populated, for round-trip tests."""
    return make_candidate(
        contact=ContactInfo(
            email="jane.doe@example.com",
            phone="+1-555-0100",
            location="Remote",
        ),
        skills=["python", "sql"],
        languages=["english"],
        experiences=[
            WorkExperience(
                company="Acme Corp",
                title="Engineer",
                start_date=date(2020, 1, 1),
                end_date=date(2022, 1, 1),
            )
        ],
        education=[
            Education(
                institution="State University",
                degree="B.Sc.",
                field_of_study="Computer Science",
            )
        ],
    )
