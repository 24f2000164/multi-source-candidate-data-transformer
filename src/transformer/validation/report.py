"""The ``ValidationReport`` produced by every validation-engine run."""

from pydantic import BaseModel, ConfigDict, Field

from transformer.validation.rule import Severity, ValidationIssue

_BLOCKING_SEVERITIES = frozenset({Severity.ERROR, Severity.CRITICAL})


class ValidationReport(BaseModel):
    """Full result of one validation-engine run.

    Attributes:
        issues: Every issue found, in rule-execution order.
        rules_executed: Names of all rules that ran.
        rules_failed: Names of rules that raised at least one issue.
        errors: Subset of ``issues`` with severity ERROR or CRITICAL.
        warnings: Subset of ``issues`` with severity INFO or WARNING.
        execution_time_ms: Total wall-clock time for the run, in milliseconds.
        is_valid: ``False`` if any ERROR/CRITICAL issue was found.
        summary: One-line human-readable rollup.
        config_version: Version of ``validation_rules.yaml`` used.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    issues: tuple[ValidationIssue, ...] = ()
    rules_executed: tuple[str, ...] = ()
    rules_failed: tuple[str, ...] = ()
    errors: tuple[ValidationIssue, ...] = ()
    warnings: tuple[ValidationIssue, ...] = ()
    execution_time_ms: float = Field(..., ge=0.0)
    is_valid: bool = True
    summary: str = ""
    config_version: str = ""

    @classmethod
    def from_issues(
        cls,
        issues: list[ValidationIssue],
        *,
        rules_executed: list[str],
        rules_failed: list[str],
        execution_time_ms: float,
        config_version: str,
    ) -> "ValidationReport":
        """Build a ``ValidationReport`` from a flat list of issues.

        Args:
            issues: Every issue found during the run.
            rules_executed: Names of all rules that ran.
            rules_failed: Names of rules that raised at least one issue.
            execution_time_ms: Total wall-clock time for the run.
            config_version: Version of the validation config used.

        Returns:
            The assembled, immutable ``ValidationReport``.
        """
        errors = tuple(i for i in issues if i.severity in _BLOCKING_SEVERITIES)
        warnings = tuple(i for i in issues if i.severity not in _BLOCKING_SEVERITIES)
        is_valid = len(errors) == 0
        summary = (
            f"{'PASS' if is_valid else 'FAIL'}: "
            f"{len(errors)} error(s), {len(warnings)} warning(s) "
            f"across {len(rules_executed)} rule(s)"
        )
        return cls(
            issues=tuple(issues),
            rules_executed=tuple(rules_executed),
            rules_failed=tuple(rules_failed),
            errors=errors,
            warnings=warnings,
            execution_time_ms=execution_time_ms,
            is_valid=is_valid,
            summary=summary,
            config_version=config_version,
        )
