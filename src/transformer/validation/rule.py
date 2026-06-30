"""Core validation contracts: ``ValidationRule``, ``Severity``, ``ValidationIssue``."""

from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from transformer.models import Candidate


class Severity(StrEnum):
    """How serious a validation issue is.

    Attributes:
        INFO: Informational only; does not affect ``is_valid``.
        WARNING: Worth surfacing but not blocking.
        ERROR: Blocking; record should not be treated as valid.
        CRITICAL: Blocking and indicates a defensive/security-relevant
            failure (e.g. an invariant pydantic should already enforce).
    """

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ValidationIssue(BaseModel):
    """A single problem found by a ``ValidationRule``.

    Attributes:
        rule_name: Name of the rule that raised this issue.
        severity: How serious the issue is.
        field: Canonical (dotted) field name the issue relates to, or
            ``None`` for record-level issues.
        message: Human-readable description of the problem.
        suggestion: Optional human-readable suggestion for how to fix it.
        candidate_value: Safe ``repr()`` of the offending value, for
            debugging (kept as a string so the report stays cheaply
            serialisable for arbitrarily nested values).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_name: str
    severity: Severity
    field: str | None = None
    message: str
    suggestion: str | None = None
    candidate_value: str | None = None


@runtime_checkable
class ValidationRule(Protocol):
    """A single, independent check against a ``Candidate``.

    Implementations must never raise for malformed/partial candidates --
    they should report an issue (or no issue) instead, since the engine's
    job is to surface problems, not to crash on them.
    """

    name: str
    severity: Severity

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Run this rule against ``candidate``.

        Args:
            candidate: The candidate record to validate.

        Returns:
            Zero or more ``ValidationIssue`` instances found.
        """
        ...
