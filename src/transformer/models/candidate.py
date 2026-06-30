"""Root canonical candidate model representing the complete transformation target."""

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from transformer.models._validators import deduplicate_strings, strip_non_empty
from transformer.models.confidence import OverallConfidence
from transformer.models.contact import ContactInfo
from transformer.models.education import Certification, Education
from transformer.models.experience import WorkExperience
from transformer.models.provenance import FieldProvenance


class Candidate(BaseModel):
    """The canonical representation of a candidate after data transformation.

    This is the central data structure of the pipeline.  It is produced by the
    merge engine from one or more parsed source records and consumed by the
    confidence engine, validation layer, and projection engine.

    Attributes:
        id: Unique identifier for this canonical record.
        first_name: Candidate's first (given) name.
        last_name: Candidate's last (family) name.
        external_id: Opaque identifier from an external source system.
        contact: Contact details (email, phone, URLs, location).
        experiences: Ordered list of work experience entries.
        education: Ordered list of academic credentials.
        skills: Deduplicated list of canonical skill tags.
        certifications: Deduplicated list of professional certifications.
        languages: Deduplicated list of spoken languages.
        confidence: Overall and per-field confidence scores.
        provenance: Per-field provenance records keyed by canonical field name.
        schema_version: Version of the canonical schema in use.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique record identifier.",
    )
    first_name: str = Field(..., description="Candidate's first name.")
    last_name: str = Field(..., description="Candidate's last name.")
    external_id: str | None = Field(
        None,
        description=(
            "Opaque identifier assigned by an external source system "
            "(e.g. ATS candidate_id). Distinct from the internal UUID `id`."
        ),
    )
    contact: ContactInfo | None = Field(None, description="Contact information.")
    experiences: list[WorkExperience] = Field(
        default_factory=list,
        max_length=200,
        description="Work experience entries.",
    )
    education: list[Education] = Field(
        default_factory=list,
        max_length=50,
        description="Academic credentials.",
    )
    skills: list[str] = Field(
        default_factory=list,
        max_length=500,
        description="Canonical skill tags.",
    )
    certifications: list[Certification] = Field(
        default_factory=list,
        max_length=100,
        description="Professional certifications.",
    )
    languages: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Spoken languages.",
    )
    confidence: OverallConfidence | None = Field(
        None,
        description="Confidence scores for this record.",
    )
    provenance: dict[str, FieldProvenance] = Field(
        default_factory=dict,
        description="Per-field provenance, keyed by canonical field name.",
    )
    schema_version: str = Field(
        default="1.0",
        description="Canonical schema version.",
    )

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def _validate_name(cls, v: Any) -> Any:
        """Strip whitespace and reject blank name fields.

        Args:
            v: Raw field value.

        Returns:
            Stripped non-blank string.

        Raises:
            ValueError: If the name is blank after stripping.
        """
        return strip_non_empty(v)

    @field_validator("external_id", mode="before")
    @classmethod
    def _validate_external_id(cls, v: Any) -> Any:
        """Strip whitespace and reject blank external_id strings.

        Args:
            v: Raw field value.

        Returns:
            Stripped string, or ``None`` if ``v`` is ``None``.

        Raises:
            ValueError: If a non-``None`` value is blank after stripping.
        """
        if v is None:
            return v
        return strip_non_empty(v)

    @field_validator("schema_version", mode="before")
    @classmethod
    def _validate_schema_version(cls, v: Any) -> Any:
        """Strip whitespace and reject blank schema version strings.

        Args:
            v: Raw schema version value.

        Returns:
            Stripped non-blank string.

        Raises:
            ValueError: If the value is blank after stripping.
        """
        return strip_non_empty(v)

    @field_validator("skills", "languages", mode="before")
    @classmethod
    def _dedup_string_lists(cls, v: Any) -> Any:
        """Deduplicate string list fields while preserving insertion order.

        Args:
            v: Raw list value.

        Returns:
            Deduplicated list of non-blank strings.
        """
        return deduplicate_strings(v)

    @field_validator("certifications", mode="before")
    @classmethod
    def _dedup_certifications(cls, v: Any) -> Any:
        """Deduplicate certifications by name (case-insensitive) preserving order.

        Args:
            v: Raw certifications list (dicts or ``Certification`` instances).

        Returns:
            Deduplicated list of certification items.
        """
        if not isinstance(v, list):
            return v
        seen: set[str] = set()
        result: list[Any] = []
        for item in v:
            if isinstance(item, dict):
                key = str(item.get("name", "")).strip().lower()
            else:
                key = str(getattr(item, "name", "")).strip().lower()
            if key and key not in seen:
                seen.add(key)
                result.append(item)
        return result
