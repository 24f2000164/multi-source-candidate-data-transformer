"""Shared builders for transformer.merge unit/integration tests."""

from datetime import UTC, date, datetime
from typing import Any

from transformer.models import Candidate, ContactInfo, DataSource, FieldProvenance

NOW = datetime.now(UTC)


def provenance_for(
    source: DataSource, fields: dict[str, Any]
) -> dict[str, FieldProvenance]:
    """Build a provenance dict for every key in ``fields``."""
    return {
        name: FieldProvenance(source=source, raw_value=str(value), extracted_at=NOW)
        for name, value in fields.items()
    }


def make_candidate(
    source: DataSource,
    *,
    first_name: str = "Jane",
    last_name: str = "Doe",
    external_id: str | None = None,
    contact: ContactInfo | None = None,
    skills: list[str] | None = None,
    languages: list[str] | None = None,
    experiences: list[Any] | None = None,
    education: list[Any] | None = None,
    certifications: list[Any] | None = None,
) -> Candidate:
    """Build a single-source ``Candidate`` with provenance for every set field."""
    raw_fields: dict[str, Any] = {"first_name": first_name, "last_name": last_name}
    kwargs: dict[str, Any] = {"first_name": first_name, "last_name": last_name}

    if external_id is not None:
        kwargs["external_id"] = external_id
        raw_fields["external_id"] = external_id
    if contact is not None:
        kwargs["contact"] = contact
        for attr in ("email", "phone", "location", "linkedin_url", "github_url"):
            value = getattr(contact, attr)
            if value is not None:
                raw_fields[attr] = value
    if skills is not None:
        kwargs["skills"] = skills
        raw_fields["skills"] = skills
    if languages is not None:
        kwargs["languages"] = languages
        raw_fields["languages"] = languages
    if experiences is not None:
        kwargs["experiences"] = experiences
        raw_fields["experiences"] = experiences
    if education is not None:
        kwargs["education"] = education
        raw_fields["education"] = education
    if certifications is not None:
        kwargs["certifications"] = certifications
        raw_fields["certifications"] = certifications

    kwargs["provenance"] = provenance_for(source, raw_fields)
    return Candidate(**kwargs)


__all__ = ["NOW", "date", "make_candidate", "provenance_for"]
