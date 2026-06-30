"""Pre-mapping schema validation for raw ATS JSON dictionaries.

Operates purely on ``dict`` data -- no file I/O, no Pydantic model
construction.  This is the cheap, fast-fail gate that runs before the
canonical mapping layer.  Unknown fields are collected (not rejected) so the
caller can log them as warnings without failing the parse.
"""

from dataclasses import dataclass, field
import logging
from typing import Any

from transformer.parsers.exceptions import SchemaValidationError

logger = logging.getLogger(__name__)

_REQUIRED_STRING_FIELDS: tuple[str, ...] = ("first_name", "last_name")

_KNOWN_TOP_LEVEL_FIELDS: frozenset[str] = frozenset(
    {
        "candidate_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "location",
        "linkedin_url",
        "github_url",
        "skills",
        "experience",
        "education",
        "certifications",
        "languages",
    }
)

_LIST_FIELDS: tuple[str, ...] = (
    "skills",
    "experience",
    "education",
    "certifications",
    "languages",
)

_MAX_STRING_LENGTH: int = 10_000


@dataclass(frozen=True)
class SchemaValidationResult:
    """Outcome of schema validation against a raw ATS JSON dict.

    Attributes:
        unknown_fields: Top-level field names present in the input but not
            part of the known ATS schema. Safe to ignore during mapping.
    """

    unknown_fields: tuple[str, ...] = field(default_factory=tuple)


class SchemaValidator:
    """Validates the shape of a raw ATS JSON dictionary.

    Stateless and side-effect free aside from logging; safe to share across
    threads.
    """

    def validate(self, data: dict[str, Any]) -> SchemaValidationResult:
        """Validate ``data`` against the required ATS JSON schema.

        Args:
            data: The raw, JSON-decoded ATS record.

        Returns:
            A ``SchemaValidationResult`` describing any unknown fields
            found (for warning-level logging by the caller).

        Raises:
            SchemaValidationError: If ``data`` is not a JSON object, a
                required field is missing, null, blank, or of the wrong
                type, or a known field has an incorrect top-level type.
        """
        if not isinstance(data, dict):
            raise SchemaValidationError(
                f"ATS JSON root must be an object, got {type(data).__name__}"
            )

        self._validate_required_strings(data)
        self._validate_list_fields(data)
        unknown = self._collect_unknown_fields(data)

        return SchemaValidationResult(unknown_fields=unknown)

    def _validate_required_strings(self, data: dict[str, Any]) -> None:
        """Validate that required string fields are present and non-blank.

        Args:
            data: The raw ATS record.

        Raises:
            SchemaValidationError: If a required field is missing, ``None``,
                not a string, blank after stripping, or exceeds the maximum
                allowed string length.
        """
        for field_name in _REQUIRED_STRING_FIELDS:
            if field_name not in data:
                raise SchemaValidationError(f"Missing required field: {field_name}")

            value = data[field_name]
            if value is None:
                raise SchemaValidationError(f"Required field is null: {field_name}")
            if not isinstance(value, str):
                raise SchemaValidationError(
                    f"Field '{field_name}' must be a string, "
                    f"got {type(value).__name__}"
                )
            if not value.strip():
                raise SchemaValidationError(f"Required field is blank: {field_name}")
            if len(value) > _MAX_STRING_LENGTH:
                raise SchemaValidationError(
                    f"Field '{field_name}' exceeds maximum length of "
                    f"{_MAX_STRING_LENGTH} characters"
                )

    def _validate_list_fields(self, data: dict[str, Any]) -> None:
        """Validate that known list-typed fields, if present, are lists.

        Args:
            data: The raw ATS record.

        Raises:
            SchemaValidationError: If a known list field is present but not
                a list, or if an item within a list field is not a JSON
                object (for object-list fields) or not a string (for
                ``skills``/``languages``).
        """
        for field_name in _LIST_FIELDS:
            if field_name not in data or data[field_name] is None:
                continue
            value = data[field_name]
            if not isinstance(value, list):
                raise SchemaValidationError(
                    f"Field '{field_name}' must be an array, "
                    f"got {type(value).__name__}"
                )
            if field_name in ("skills", "languages"):
                for item in value:
                    if not isinstance(item, str):
                        raise SchemaValidationError(
                            f"Field '{field_name}' must contain only strings"
                        )
            else:
                for item in value:
                    if not isinstance(item, dict):
                        raise SchemaValidationError(
                            f"Field '{field_name}' must contain only objects"
                        )

    def _collect_unknown_fields(self, data: dict[str, Any]) -> tuple[str, ...]:
        """Collect top-level keys not part of the known ATS schema.

        Args:
            data: The raw ATS record.

        Returns:
            A tuple of unknown top-level field names, in encounter order.
        """
        unknown = tuple(k for k in data if k not in _KNOWN_TOP_LEVEL_FIELDS)
        if unknown:
            logger.warning("ats_unknown_fields_detected", extra={"fields": unknown})
        return unknown
