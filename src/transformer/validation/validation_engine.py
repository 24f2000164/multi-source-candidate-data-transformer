"""``ValidationEngine``: orchestrates a ``RuleRegistry`` against a ``Candidate``."""

import time

from transformer.models import Candidate
from transformer.validation.report import ValidationReport
from transformer.validation.rule_registry import RuleRegistry


class ValidationEngine:
    """Runs every registered rule against a candidate and builds a report.

    Has no hardcoded validator list -- it only knows about ``RuleRegistry``.
    Adding a new rule never requires a change here (Open/Closed); it only
    requires adding the rule to the registry's construction.
    """

    def __init__(
        self, registry: RuleRegistry, *, config_version: str = ""
    ) -> None:
        """Initialise the engine with its rule registry.

        Args:
            registry: The ``RuleRegistry`` whose rules will be executed.
            config_version: Version string recorded in the resulting report.
        """
        self._registry = registry
        self._config_version = config_version

    def run(self, candidate: Candidate) -> ValidationReport:
        """Run every registered rule against ``candidate``.

        Args:
            candidate: The candidate record to validate.

        Returns:
            A ``ValidationReport`` summarising every issue found, with
            timing captured via ``time.perf_counter``.
        """
        start = time.perf_counter()

        issues = []
        rules_executed: list[str] = []
        rules_failed: list[str] = []

        for rule in self._registry.get_rules():
            rules_executed.append(rule.name)
            rule_issues = rule.check(candidate)
            if rule_issues:
                rules_failed.append(rule.name)
                issues.extend(rule_issues)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return ValidationReport.from_issues(
            issues,
            rules_executed=rules_executed,
            rules_failed=rules_failed,
            execution_time_ms=elapsed_ms,
            config_version=self._config_version,
        )
