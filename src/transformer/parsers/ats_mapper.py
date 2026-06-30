"""Explicit mapping layer: raw ATS JSON dict -> Canonical Candidate Model.

Pure functions only -- no file I/O, no logging side effects beyond what the
caller wires in.  Kept separate from ``ATSParser`` so the mapping rules are
independently testable and the orchestrator stays thin (load -> validate ->
map -> return).

Per Sprint 02 instructions, invalid *required* fields within nested objects
(experience/education/certifications) fail the entire parse -- there is no
silent per-item skipping. This keeps parsing deterministic and auditable.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from transformer.models import (
    Candidate,
    Certification,
    ContactInfo,
    DataSource,
    Education,
    FieldProvenance,
    WorkExperience,
)
from transformer.parsers.exceptions import MappingError


class ATSMapper:
    """Maps a validated raw ATS dictionary onto the Canonical Candidate Model."""

    def map_candidate(self, data: dict[str, Any]) -> Candidate:
        """Map a raw ATS JSON dictionary to a ``Candidate`` instance.

        Args:
            data: The raw, schema-validated ATS record.

        Returns:
            A fully validated ``Candidate`` instance with provenance
            populated for every field present in the source.

        Raises:
            MappingError: If construction of the canonical model fails for
                any reason, including an invalid nested object such as a
                malformed experience, education, or certification entry.
        """
        extracted_at = datetime.now(UTC)
        provenance: dict[str, FieldProvenance] = {}

        def _record(field_name: str, raw_value: Any) -> None:
            provenance[field_name] = FieldProvenance(
                source=DataSource.ATS,
                raw_value=str(raw_value),
                extracted_at=extracted_at,
            )

        try:
            kwargs: dict[str, Any] = {
                "first_name": data["first_name"],
                "last_name": data["last_name"],
            }
            _record("first_name", data["first_name"])
            _record("last_name", data["last_name"])

            external_id = data.get("candidate_id")
            if external_id is not None:
                kwargs["external_id"] = external_id
                _record("external_id", external_id)

            contact = self._map_contact(data)
            if contact is not None:
                kwargs["contact"] = contact
                for contact_field in (
                    "email",
                    "phone",
                    "location",
                    "linkedin_url",
                    "github_url",
                ):
                    if data.get(contact_field) is not None:
                        _record(contact_field, data[contact_field])

            if data.get("skills"):
                kwargs["skills"] = list(data["skills"])
                _record("skills", data["skills"])

            if data.get("languages"):
                kwargs["languages"] = list(data["languages"])
                _record("languages", data["languages"])

            if data.get("experience"):
                kwargs["experiences"] = [
                    self._map_experience(item) for item in data["experience"]
                ]
                _record("experiences", data["experience"])

            if data.get("education"):
                kwargs["education"] = [
                    self._map_education(item) for item in data["education"]
                ]
                _record("education", data["education"])

            if data.get("certifications"):
                kwargs["certifications"] = [
                    self._map_certification(item) for item in data["certifications"]
                ]
                _record("certifications", data["certifications"])

            kwargs["provenance"] = provenance

            return Candidate(**kwargs)

        except ValidationError as exc:
            raise MappingError(
                "Failed to map ATS record to canonical Candidate model: "
                f"{self._summarise_validation_error(exc)}"
            ) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise MappingError(
                f"Failed to map ATS record to canonical Candidate model: {exc}"
            ) from exc

    def _map_contact(self, data: dict[str, Any]) -> ContactInfo | None:
        """Map ATS contact-related fields to a ``ContactInfo`` instance.

        Args:
            data: The raw ATS record.

        Returns:
            A ``ContactInfo`` instance, or ``None`` if no contact fields are
            present in the source data.

        Raises:
            ValidationError: If a present contact field fails Pydantic
                validation (e.g. malformed email or URL).
        """
        contact_fields = (
            "email",
            "phone",
            "location",
            "linkedin_url",
            "github_url",
        )
        present = {f: data[f] for f in contact_fields if data.get(f) is not None}
        if not present:
            return None
        return ContactInfo(**present)

    def _map_experience(self, item: dict[str, Any]) -> WorkExperience:
        """Map a single raw ATS experience entry to ``WorkExperience``.

        Args:
            item: A raw experience object from the ATS ``experience`` array.

        Returns:
            A validated ``WorkExperience`` instance.

        Raises:
            MappingError: If the entry is missing a required field
                (``company``, ``title``, ``start_date``).
            ValidationError: If a present field contains an invalid value.
        """
        return WorkExperience(
            company=self._required(item, "company"),
            title=self._required(item, "title"),
            # start_date is extracted as str; Pydantic coerces ISO-8601
            # date strings to `date` at construction time, or raises
            # ValidationError if the format is invalid.
            start_date=self._required(item, "start_date"),  # type: ignore[arg-type]
            end_date=item.get("end_date"),
            description=item.get("description"),
            skills=list(item.get("skills") or []),
        )

    def _map_education(self, item: dict[str, Any]) -> Education:
        """Map a single raw ATS education entry to ``Education``.

        Args:
            item: A raw education object from the ATS ``education`` array.

        Returns:
            A validated ``Education`` instance.

        Raises:
            MappingError: If the entry is missing a required field
                (``institution``, ``degree``).
            ValidationError: If a present field contains an invalid value.
        """
        return Education(
            institution=self._required(item, "institution"),
            degree=self._required(item, "degree"),
            field_of_study=item.get("field_of_study"),
            start_date=item.get("start_date"),
            end_date=item.get("end_date"),
            gpa=item.get("gpa"),
        )

    def _map_certification(self, item: dict[str, Any]) -> Certification:
        """Map a single raw ATS certification entry to ``Certification``.

        Args:
            item: A raw certification object from the ATS
                ``certifications`` array.

        Returns:
            A validated ``Certification`` instance.

        Raises:
            MappingError: If the entry is missing the required ``name``
                field.
            ValidationError: If a present field contains an invalid value.
        """
        return Certification(
            name=self._required(item, "name"),
            issuer=item.get("issuer"),
            issued_date=item.get("issued_date"),
            expiry_date=item.get("expiry_date"),
        )

    @staticmethod
    def _required(item: dict[str, Any], field_name: str) -> str:
        """Extract a required string field from a nested raw object.

        Args:
            item: The raw nested object (experience/education/certification
                entry).
            field_name: The key to extract.

        Returns:
            The value at ``field_name`` as a string.

        Raises:
            MappingError: If the field is absent, ``None``, or not a
                string. This ensures invalid nested required objects fail
                the entire candidate parse deterministically rather than
                being silently skipped.
        """
        value = item.get(field_name)
        if not isinstance(value, str):
            raise MappingError(
                f"Required nested field '{field_name}' is missing or invalid"
            )
        return value

    @staticmethod
    def _summarise_validation_error(exc: ValidationError) -> str:
        """Build a short, safe summary of a Pydantic ``ValidationError``.

        Args:
            exc: The raised Pydantic validation error.

        Returns:
            A comma-separated ``field: message`` summary, safe to surface
            to callers (no raw traceback).
        """
        parts = [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        ]
        return "; ".join(parts)
