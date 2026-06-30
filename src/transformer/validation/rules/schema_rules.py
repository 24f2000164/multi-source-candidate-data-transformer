"""Schema-level validation rules: structural/type invariants on a ``Candidate``.

These are mostly defense-in-depth: pydantic already enforces most of these
invariants at construction time (frozen models, ``ge``/``le`` constraints,
``EmailStr``, etc). They are re-checked here because (a) a ``Candidate``
could in principle be constructed via ``model_construct`` bypassing
validation, and (b) the validation report is a useful single place to see
*all* problems with a record, schema-level or not.
"""

import math
import unicodedata
from uuid import UUID

from transformer.models import Candidate
from transformer.validation.rule import Severity, ValidationIssue

_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})
_MAX_STRING_LENGTH = 10_000


class RequiredFieldsRule:
    """Confirms required identity fields are present and non-blank."""

    name = "required_fields"
    severity = Severity.ERROR

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check that ``first_name`` and ``last_name`` are non-blank.

        Args:
            candidate: The candidate record to validate.

        Returns:
            Issues for any blank required field (in practice unreachable
            via the pydantic model, included for defense in depth).
        """
        issues: list[ValidationIssue] = []
        for field in ("first_name", "last_name"):
            value = getattr(candidate, field, None)
            if not value or not str(value).strip():
                issues.append(
                    ValidationIssue(
                        rule_name=self.name,
                        severity=self.severity,
                        field=field,
                        message=f"required field '{field}' is empty",
                        suggestion=f"provide a non-blank value for '{field}'",
                    )
                )
        return issues


class SchemaVersionRule:
    """Confirms ``schema_version`` is one this codebase recognises."""

    name = "schema_version"
    severity = Severity.ERROR

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check ``candidate.schema_version`` against the supported set.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue if the schema version is unrecognised, else none.
        """
        if candidate.schema_version not in _SUPPORTED_SCHEMA_VERSIONS:
            return [
                ValidationIssue(
                    rule_name=self.name,
                    severity=self.severity,
                    field="schema_version",
                    message=(
                        f"unrecognised schema_version '{candidate.schema_version}'"
                    ),
                    suggestion=(
                        "use one of: " + ", ".join(sorted(_SUPPORTED_SCHEMA_VERSIONS))
                    ),
                    candidate_value=repr(candidate.schema_version),
                )
            ]
        return []


class ConfidenceValueRule:
    """Catches NaN/Infinity/negative-zero/out-of-range confidence values.

    Defense in depth: ``FieldConfidence``/``OverallConfidence`` already
    reject these via pydantic validators, so this rule should never fire on
    a properly constructed ``Candidate``.
    """

    name = "confidence_values"
    severity = Severity.CRITICAL

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check overall and per-field confidence scores for invalid values.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue per invalid confidence score found.
        """
        if candidate.confidence is None:
            return []

        issues: list[ValidationIssue] = []
        issues.extend(
            self._check_score("confidence.score", candidate.confidence.score)
        )
        for field_name, field_confidence in candidate.confidence.fields.items():
            issues.extend(
                self._check_score(
                    f"confidence.fields.{field_name}", field_confidence.score
                )
            )
        return issues

    def _check_score(self, field: str, score: float) -> list[ValidationIssue]:
        """Validate a single confidence score value.

        Args:
            field: Dotted path to the score, used in the issue.
            score: The score value to validate.

        Returns:
            One issue if invalid, else an empty list.
        """
        is_negative_zero = score == 0.0 and math.copysign(1.0, score) < 0
        if not math.isfinite(score) or score < 0.0 or score > 1.0 or is_negative_zero:
            return [
                ValidationIssue(
                    rule_name=self.name,
                    severity=self.severity,
                    field=field,
                    message=f"invalid confidence value: {score!r}",
                    suggestion="confidence values must be finite and in [0.0, 1.0]",
                    candidate_value=repr(score),
                )
            ]
        return []


class StringLengthRule:
    """Flags strings beyond the configured maximum length."""

    name = "string_length"
    severity = Severity.ERROR

    def __init__(self, *, max_length: int = _MAX_STRING_LENGTH) -> None:
        """Initialise with the configured maximum string length.

        Args:
            max_length: Maximum allowed length for any checked string field.
        """
        self._max_length = max_length

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check name fields and free-text descriptions for excessive length.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue per string field exceeding ``max_length``.
        """
        issues: list[ValidationIssue] = []
        candidates_to_check: list[tuple[str, str | None]] = [
            ("first_name", candidate.first_name),
            ("last_name", candidate.last_name),
        ]
        for i, exp in enumerate(candidate.experiences):
            candidates_to_check.append((f"experiences[{i}].description", exp.description))
        for field, value in candidates_to_check:
            if value is not None and len(value) > self._max_length:
                issues.append(
                    ValidationIssue(
                        rule_name=self.name,
                        severity=self.severity,
                        field=field,
                        message=(
                            f"'{field}' exceeds max length "
                            f"({len(value)} > {self._max_length})"
                        ),
                        suggestion="truncate or split the field before ingest",
                    )
                )
        return issues


class UnicodeConfusableRule:
    """Flags non-Latin/confusable Unicode characters in name fields.

    Heuristic: a name field is flagged if it mixes Latin letters with
    characters from other scripts known to contain visually-confusable
    homoglyphs (e.g. Cyrillic 'а' vs Latin 'a'), which can be used to spoof
    a different identity.
    """

    name = "unicode_confusables"
    severity = Severity.WARNING

    _CONFUSABLE_SCRIPT_PREFIXES = ("CYRILLIC", "GREEK")

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check ``first_name``/``last_name`` for mixed-script confusables.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue per name field containing suspicious mixed scripts.
        """
        issues: list[ValidationIssue] = []
        for field in ("first_name", "last_name"):
            value = getattr(candidate, field)
            if self._has_mixed_confusable_script(value):
                issues.append(
                    ValidationIssue(
                        rule_name=self.name,
                        severity=self.severity,
                        field=field,
                        message=f"'{field}' mixes Latin and confusable scripts",
                        suggestion="verify the name was not spoofed with homoglyphs",
                        candidate_value=repr(value),
                    )
                )
        return issues

    def _has_mixed_confusable_script(self, value: str) -> bool:
        """Detect whether ``value`` mixes Latin letters with confusable scripts.

        Args:
            value: The string to inspect.

        Returns:
            ``True`` if both Latin and a confusable script appear.
        """
        has_latin = False
        has_confusable = False
        for ch in value:
            if not ch.isalpha():
                continue
            try:
                name = unicodedata.name(ch)
            except ValueError:
                continue
            if name.startswith("LATIN"):
                has_latin = True
            elif name.startswith(self._CONFUSABLE_SCRIPT_PREFIXES):
                has_confusable = True
        return has_latin and has_confusable


class IdRule:
    """Confirms ``candidate.id`` is a valid UUID (defensive, schema-level)."""

    name = "id_uuid"
    severity = Severity.CRITICAL

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check that ``candidate.id`` is a ``UUID`` instance.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue if ``id`` is not a valid ``UUID``, else none. In
            practice unreachable via the pydantic model; included as a
            defensive, security-relevant check.
        """
        if not isinstance(candidate.id, UUID):
            return [
                ValidationIssue(
                    rule_name=self.name,
                    severity=self.severity,
                    field="id",
                    message="candidate id is not a valid UUID",
                    candidate_value=repr(candidate.id),
                )
            ]
        return []
