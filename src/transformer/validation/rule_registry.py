"""``RuleRegistry``: constructor-injected, immutable set of validation rules."""

from transformer.validation.exceptions import DuplicateRuleNameError
from transformer.validation.rule import ValidationRule


class RuleRegistry:
    """Holds the rules a ``ValidationEngine`` will run.

    No global/module-level state: a registry is built by passing in the
    list of rule instances to use. Adding a new rule means adding it to that
    constructor list (typically in pipeline/CLI wiring) -- ``ValidationEngine``
    itself never changes (Open/Closed).
    """

    def __init__(self, rules: list[ValidationRule]) -> None:
        """Initialise the registry with its rule instances.

        Args:
            rules: The rules this registry will expose, in execution order.

        Raises:
            DuplicateRuleNameError: If two rules share the same ``name``,
                which would otherwise cause a rule to silently run twice
                under one identity (and once under another).
        """
        seen: set[str] = set()
        for rule in rules:
            if rule.name in seen:
                raise DuplicateRuleNameError(
                    f"duplicate validation rule name: {rule.name!r}"
                )
            seen.add(rule.name)
        self._rules: tuple[ValidationRule, ...] = tuple(rules)

    def get_rules(self) -> tuple[ValidationRule, ...]:
        """Return the registered rules, in execution order.

        Returns:
            An immutable tuple of rules (empty if none registered).
        """
        return self._rules
