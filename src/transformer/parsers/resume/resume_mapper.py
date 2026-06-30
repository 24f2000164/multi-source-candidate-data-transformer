"""Explicit mapping layer: ExtractedResumeData -> Canonical Candidate Model.

Pure mapping only -- never touches raw text, regex, or files. Mirrors
``ATSMapper``'s overall shape, but diverges deliberately on one point:
unlike ATS JSON (structured, all-or-nothing failure is appropriate because
any invalid entry signals a genuine data-quality problem upstream), resume
field extraction is inherently heuristic. A single mis-segmented experience
or education entry should not discard an otherwise-good candidate profile,
so invalid nested entries are skipped with a logged warning rather than
failing the whole parse (per-entry graceful degradation).
"""

from datetime import UTC, date, datetime
import logging
from typing import Any

from dateutil import parser as dateutil_parser
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
from transformer.parsers.resume.extracted_data import (
    ExtractedResumeData,
    RawCertificationEntry,
    RawEducationEntry,
    RawExperienceEntry,
)

logger = logging.getLogger(__name__)


class ResumeMapper:
    """Maps a typed ``ExtractedResumeData`` instance to the Canonical Model."""

    def map_candidate(self, data: ExtractedResumeData) -> Candidate:
        """Map extracted resume data to a ``Candidate`` instance.

        Args:
            data: The typed intermediate extraction result.

        Returns:
            A fully validated ``Candidate`` instance with provenance
            populated for every populated field.

        Raises:
            MappingError: If construction of the canonical model fails,
                including an invalid required nested entry (e.g. an
                experience entry missing company/title/start_date).
        """
        if not data.first_name or not data.last_name:
            raise MappingError("Unable to detect candidate name")

        extracted_at = datetime.now(UTC)
        provenance: dict[str, FieldProvenance] = {}

        def _record(field_name: str, raw_value: Any) -> None:
            provenance[field_name] = FieldProvenance(
                source=DataSource.RESUME,
                raw_value=str(raw_value),
                extracted_at=extracted_at,
            )

        try:
            kwargs: dict[str, Any] = {
                "first_name": data.first_name,
                "last_name": data.last_name,
            }
            _record("first_name", data.first_name)
            _record("last_name", data.last_name)

            contact = self._map_contact(data)
            if contact is not None:
                kwargs["contact"] = contact
                for field_name in (
                    "email",
                    "phone",
                    "location",
                    "linkedin_url",
                    "github_url",
                ):
                    value = getattr(data, field_name)
                    if value is not None:
                        _record(field_name, value)

            if data.skills:
                kwargs["skills"] = list(data.skills)
                _record("skills", data.skills)

            if data.languages:
                kwargs["languages"] = list(data.languages)
                _record("languages", data.languages)

            if data.experience_entries:
                experiences = self._map_entries_gracefully(
                    data.experience_entries, self._map_experience, "experience"
                )
                if experiences:
                    kwargs["experiences"] = experiences
                    _record("experiences", data.experience_entries)

            if data.education_entries:
                education = self._map_entries_gracefully(
                    data.education_entries, self._map_education, "education"
                )
                if education:
                    kwargs["education"] = education
                    _record("education", data.education_entries)

            if data.certifications:
                certifications = self._map_entries_gracefully(
                    data.certifications, self._map_certification, "certification"
                )
                if certifications:
                    kwargs["certifications"] = certifications
                    _record("certifications", data.certifications)

            kwargs["provenance"] = provenance

            return Candidate(**kwargs)

        except ValidationError as exc:
            raise MappingError(
                "Failed to map resume record to canonical Candidate model: "
                f"{self._summarise_validation_error(exc)}"
            ) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise MappingError(
                f"Failed to map resume record to canonical Candidate model: {exc}"
            ) from exc

    @staticmethod
    def _map_entries_gracefully(
        items: list[Any],
        single_mapper: Any,
        entry_kind: str,
    ) -> list[Any]:
        """Map a list of raw entries, skipping (not failing on) invalid ones.

        Args:
            items: Raw extracted entries (experience/education/
                certification).
            single_mapper: Bound method that maps one raw entry to its
                canonical model, raising ``MappingError`` on invalid
                required fields.
            entry_kind: Human-readable entry type, for the warning log.

        Returns:
            The successfully mapped entries, in original order. Entries
            that failed to map are omitted, not raised.
        """
        mapped: list[Any] = []
        for index, item in enumerate(items):
            try:
                mapped.append(single_mapper(item))
            except MappingError as exc:
                logger.warning(
                    "resume_entry_skipped",
                    extra={
                        "entry_kind": entry_kind,
                        "entry_index": index,
                        "reason": exc.message,
                    },
                )
        return mapped

    def _map_contact(self, data: ExtractedResumeData) -> ContactInfo | None:
        """Map extracted contact fields to a ``ContactInfo`` instance.

        Args:
            data: The typed intermediate extraction result.

        Returns:
            A ``ContactInfo`` instance, or ``None`` if no contact fields
            were extracted.
        """
        present = {
            f: getattr(data, f)
            for f in ("email", "phone", "location", "linkedin_url", "github_url")
            if getattr(data, f) is not None
        }
        if not present:
            return None
        return ContactInfo(**present)

    def _map_experience(self, item: RawExperienceEntry) -> WorkExperience:
        """Map a single raw experience entry to ``WorkExperience``.

        Args:
            item: A raw, extracted experience entry.

        Returns:
            A validated ``WorkExperience`` instance.

        Raises:
            MappingError: If a required field (``company``, ``title``,
                ``start_date``) is missing or unparseable.
        """
        return WorkExperience(
            company=self._required(item.company, "company"),
            title=self._required(item.title, "title"),
            start_date=self._required_date(item.start_date, "start_date"),
            end_date=self._optional_date(item.end_date),
            description=item.description,
        )

    def _map_education(self, item: RawEducationEntry) -> Education:
        """Map a single raw education entry to ``Education``.

        Args:
            item: A raw, extracted education entry.

        Returns:
            A validated ``Education`` instance.

        Raises:
            MappingError: If a required field (``institution``, ``degree``)
                is missing.
        """
        return Education(
            institution=self._required(item.institution, "institution"),
            degree=self._required(item.degree, "degree"),
            field_of_study=item.field_of_study,
            start_date=self._optional_date(item.start_date),
            end_date=self._optional_date(item.end_date),
            gpa=item.gpa,
        )

    def _map_certification(self, item: RawCertificationEntry) -> Certification:
        """Map a single raw certification entry to ``Certification``.

        Args:
            item: A raw, extracted certification entry.

        Returns:
            A validated ``Certification`` instance.

        Raises:
            MappingError: If the required ``name`` field is missing.
        """
        return Certification(
            name=self._required(item.name, "name"),
            issuer=item.issuer,
            issued_date=self._optional_date(item.issued_date),
            expiry_date=self._optional_date(item.expiry_date),
        )

    @staticmethod
    def _required(value: str | None, field_name: str) -> str:
        """Extract a required string field, failing the parse if absent.

        Args:
            value: The candidate value.
            field_name: Name of the field, for the error message.

        Returns:
            The value, guaranteed non-``None``.

        Raises:
            MappingError: If ``value`` is ``None`` or blank.
        """
        if not value or not value.strip():
            raise MappingError(
                f"Required nested field '{field_name}' is missing or invalid"
            )
        return value

    @staticmethod
    def _required_date(value: str | None, field_name: str) -> date:
        """Parse a required raw date string into a ``date``.

        Args:
            value: The raw, extracted date string.
            field_name: Name of the field, for the error message.

        Returns:
            The parsed date.

        Raises:
            MappingError: If ``value`` is absent or cannot be parsed.
        """
        if not value:
            raise MappingError(
                f"Required nested field '{field_name}' is missing or invalid"
            )
        parsed = ResumeMapper._optional_date(value)
        if parsed is None:
            raise MappingError(f"Unable to parse date for '{field_name}': {value}")
        return parsed

    @staticmethod
    def _optional_date(value: str | None) -> date | None:
        """Best-effort parse of a free-form date string into a ``date``.

        Args:
            value: The raw, extracted date string, or ``None``.

        Returns:
            The parsed date, or ``None`` if ``value`` is ``None``/blank or
            unparseable (e.g. ``"Present"``/``"Current"``).
        """
        if not value or not value.strip():
            return None
        if value.strip().lower() in {"present", "current", "now"}:
            return None
        try:
            parsed_dt = dateutil_parser.parse(value, default=datetime(1900, 1, 1))
            return parsed_dt.date()
        except (ValueError, OverflowError):
            return None

    @staticmethod
    def _summarise_validation_error(exc: ValidationError) -> str:
        """Build a short, safe summary of a Pydantic ``ValidationError``.

        Args:
            exc: The raised Pydantic validation error.

        Returns:
            A comma-separated ``field: message`` summary.
        """
        parts = [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        ]
        return "; ".join(parts)
