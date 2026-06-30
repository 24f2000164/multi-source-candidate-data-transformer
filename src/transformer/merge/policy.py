"""Merge policy: per-field strategy and source-priority configuration.

Loaded from ``config/merge_policy.yaml`` so behaviour can be tuned without
code changes (Sprint 5 requirement: "Move merge priorities into
configurable YAML rules instead of hardcoding them").
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from transformer.config.loader import DEFAULT_CONFIG_DIR, load_yaml
from transformer.merge.exceptions import MergeError
from transformer.models import DataSource
from transformer.normalizers.exceptions import NormalizationError

DEFAULT_MERGE_POLICY_PATH = DEFAULT_CONFIG_DIR / "merge_policy.yaml"

_VALID_STRATEGIES = frozenset(
    {"source_priority", "first_non_empty", "union", "highest_confidence"}
)


@dataclass(frozen=True)
class FieldRule:
    """Merge configuration for a single canonical field.

    Attributes:
        strategy: Name of the resolution strategy to apply (one of
            ``source_priority``, ``first_non_empty``, ``union``,
            ``highest_confidence``).
        priority: Ordered source priority, highest priority first.
        identity_keys: For ``union`` on structured lists, the attribute
            names used to match entries across sources. Empty for scalar
            and flat-list fields.
    """

    strategy: str
    priority: tuple[DataSource, ...]
    identity_keys: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MergePolicy:
    """Complete merge policy: a default rule plus per-field overrides.

    Attributes:
        default_rule: Rule applied to any field without an explicit entry.
        field_rules: Per-field overrides, keyed by canonical field name
            (dotted for nested ``contact.*`` fields).
    """

    default_rule: FieldRule
    field_rules: dict[str, FieldRule]

    def rule_for(self, field_name: str) -> FieldRule:
        """Look up the merge rule for a canonical field.

        Args:
            field_name: Canonical (dotted) field name, e.g. ``"skills"`` or
                ``"contact.email"``.

        Returns:
            The configured ``FieldRule``, or ``default_rule`` if the field
            has no explicit override.
        """
        return self.field_rules.get(field_name, self.default_rule)


def _parse_priority(raw: Any, *, context: str) -> tuple[DataSource, ...]:
    if not isinstance(raw, list) or not raw:
        raise MergeError(f"{context}: 'priority' must be a non-empty list")
    try:
        return tuple(DataSource(item) for item in raw)
    except ValueError as exc:
        raise MergeError(f"{context}: invalid DataSource in 'priority'") from exc


def _parse_rule(raw: Any, *, context: str) -> FieldRule:
    if not isinstance(raw, dict):
        raise MergeError(f"{context}: rule must be a mapping")
    strategy = raw.get("strategy")
    if strategy not in _VALID_STRATEGIES:
        raise MergeError(f"{context}: unknown strategy {strategy!r}")
    priority = _parse_priority(raw.get("priority"), context=context)
    identity_keys = tuple(raw.get("identity_keys") or ())
    return FieldRule(strategy=strategy, priority=priority, identity_keys=identity_keys)


def load_merge_policy(path: Path = DEFAULT_MERGE_POLICY_PATH) -> MergePolicy:
    """Load and validate the merge policy from YAML.

    Args:
        path: Path to the merge policy YAML file. Defaults to
            ``config/merge_policy.yaml`` at the repository root.

    Returns:
        The parsed, validated ``MergePolicy``.

    Raises:
        MergeError: If the file is missing/invalid, or any rule is
            malformed (unknown strategy, empty/invalid priority list).
    """
    try:
        data = load_yaml(path)
    except NormalizationError as exc:
        raise MergeError(str(exc)) from exc

    default_strategy = data.get("default_strategy")
    if default_strategy not in _VALID_STRATEGIES:
        raise MergeError(f"{path}: unknown default_strategy {default_strategy!r}")
    default_priority = _parse_priority(
        data.get("default_priority"), context=f"{path}: default_priority"
    )
    default_rule = FieldRule(strategy=default_strategy, priority=default_priority)

    raw_fields = data.get("fields") or {}
    if not isinstance(raw_fields, dict):
        raise MergeError(f"{path}: 'fields' must be a mapping")

    field_rules = {
        str(name): _parse_rule(rule, context=f"{path}: field '{name}'")
        for name, rule in raw_fields.items()
    }

    return MergePolicy(default_rule=default_rule, field_rules=field_rules)
