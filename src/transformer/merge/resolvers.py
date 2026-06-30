"""Resolver hierarchy for per-field-kind merge resolution.

``Resolver``s decide *how* a field kind is resolved (scalar vs. flat list vs.
identity-keyed structured list); the actual winner-picking logic is
delegated to a ``MergeStrategy`` (see ``transformer.merge.strategies``) so
neither layer hardcodes the other's concerns -- this keeps the design open
for extension (new field kinds, new strategies) without modification
(Open/Closed Principle).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from transformer.merge.exceptions import MergeError
from transformer.merge.identity import identity_key
from transformer.merge.policy import FieldRule
from transformer.merge.strategies import (
    FirstNonEmptyStrategy,
    HighestConfidenceStrategy,
    MergeStrategy,
    SourcePriorityStrategy,
    SourceValue,
    StrategyResult,
    UnionStrategy,
)
from transformer.models import DataSource


@dataclass(frozen=True)
class ResolutionResult:
    """The fully-described outcome of resolving one canonical field.

    Attributes:
        field: Canonical (dotted) field name.
        strategy: Name of the strategy that produced ``value``.
        value: The resolved field value.
        sources_considered: Every source that attempted to supply a value
            for this field (including empty attempts).
        contributing_sources: Sources whose non-empty value fed into
            ``value``.
        conflict: ``True`` if sources disagreed and a choice was made.
        warnings: Human-readable warnings surfaced to the ``MergeReport``.
    """

    field: str
    strategy: str
    value: Any
    sources_considered: tuple[DataSource, ...]
    contributing_sources: tuple[DataSource, ...]
    conflict: bool
    winning_source: DataSource | None = None
    warnings: tuple[str, ...] = ()


_SCALAR_STRATEGIES: dict[str, MergeStrategy] = {
    "source_priority": SourcePriorityStrategy(),
    "first_non_empty": FirstNonEmptyStrategy(),
    "highest_confidence": HighestConfidenceStrategy(),
}


class BaseResolver(ABC):
    """Abstract base for all field-kind resolvers."""

    @abstractmethod
    def resolve(
        self, field_name: str, values: list[SourceValue], rule: FieldRule
    ) -> ResolutionResult:
        """Resolve a single canonical field's value across sources.

        Args:
            field_name: Canonical (dotted) field name.
            values: One ``SourceValue`` per source that attempted to supply
                this field (empty values included).
            rule: The configured ``FieldRule`` for this field.

        Returns:
            The resolution outcome.
        """
        raise NotImplementedError

    @staticmethod
    def _considered(values: list[SourceValue]) -> tuple[DataSource, ...]:
        return tuple(v.source for v in values)


class StringResolver(BaseResolver):
    """Resolves scalar fields (strings, optional strings) via a strategy."""

    def resolve(
        self, field_name: str, values: list[SourceValue], rule: FieldRule
    ) -> ResolutionResult:
        strategy = _SCALAR_STRATEGIES.get(rule.strategy)
        if strategy is None:
            raise MergeError(
                f"field '{field_name}': strategy '{rule.strategy}' is not "
                "valid for scalar fields"
            )
        result = strategy.apply(values, rule.priority)
        warnings = (
            (f"field '{field_name}': sources disagree, used {result.winning_source}",)
            if result.conflict
            else ()
        )
        return ResolutionResult(
            field=field_name,
            strategy=strategy.name,
            value=result.value,
            sources_considered=self._considered(values),
            contributing_sources=result.contributing_sources,
            conflict=result.conflict,
            winning_source=result.winning_source,
            warnings=warnings,
        )


class ListResolver(BaseResolver):
    """Resolves flat list fields via case-insensitive union dedup."""

    def resolve(
        self, field_name: str, values: list[SourceValue], rule: FieldRule
    ) -> ResolutionResult:
        if rule.strategy != "union":
            raise MergeError(
                f"field '{field_name}': strategy '{rule.strategy}' is not "
                "valid for list fields, expected 'union'"
            )
        strategy = UnionStrategy(self._merge_flat)
        result = strategy.apply(values, rule.priority)
        return self._to_resolution(field_name, strategy, result, values)

    @staticmethod
    def _merge_flat(ordered: list[SourceValue]) -> list[Any]:
        seen: set[str] = set()
        merged: list[Any] = []
        for source_value in ordered:
            for item in source_value.value:
                key = str(item).strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    merged.append(item)
        return merged

    @staticmethod
    def _to_resolution(
        field_name: str,
        strategy: MergeStrategy,
        result: StrategyResult,
        values: list[SourceValue],
    ) -> ResolutionResult:
        return ResolutionResult(
            field=field_name,
            strategy=strategy.name,
            value=result.value,
            sources_considered=BaseResolver._considered(values),
            contributing_sources=result.contributing_sources,
            conflict=result.conflict,
            warnings=(),
        )


class StructuredListResolver(ListResolver):
    """Base for identity-keyed structured list fields (experience/education/
    certifications). Subclasses only need to declare a type name for error
    messages -- the merge algorithm is shared.
    """

    item_type_name: str = "item"

    def resolve(
        self, field_name: str, values: list[SourceValue], rule: FieldRule
    ) -> ResolutionResult:
        if rule.strategy != "union":
            raise MergeError(
                f"field '{field_name}': strategy '{rule.strategy}' is not "
                "valid for structured list fields, expected 'union'"
            )
        if not rule.identity_keys:
            raise MergeError(
                f"field '{field_name}': structured list merge requires "
                "'identity_keys' in the merge policy"
            )
        strategy = UnionStrategy(self._make_merge_fn(rule.identity_keys))
        result = strategy.apply(values, rule.priority)
        return self._to_resolution(field_name, strategy, result, values)

    @staticmethod
    def _make_merge_fn(identity_keys: tuple[str, ...]) -> Any:
        def _merge(ordered: list[SourceValue]) -> list[Any]:
            seen: dict[tuple[str, ...], Any] = {}
            merged: list[Any] = []
            for source_value in ordered:
                for item in source_value.value:
                    key = identity_key(item, identity_keys)
                    if key not in seen:
                        seen[key] = item
                        merged.append(item)
                    else:
                        existing = seen[key]
                        filled = StructuredListResolver._fill_missing_fields(
                            existing, item
                        )
                        if filled is not existing:
                            index = merged.index(existing)
                            merged[index] = filled
                            seen[key] = filled
            return merged

        return _merge

    @staticmethod
    def _fill_missing_fields(existing: Any, incoming: Any) -> Any:
        """Fill ``existing``'s blank fields from ``incoming``, never overwriting.

        Applies to any two same-type pydantic model instances that share
        an identity key (e.g. matched by institution+degree). ``existing``
        is the higher-priority (earlier-source) item and is preserved as
        the base; only fields where ``existing`` has no usable value
        (``None`` or blank string) are filled in from ``incoming``. This
        replaces "first-match-wins whole-object" with a field-level
        gap-fill, so lower-priority sources never lose data the
        higher-priority source simply didn't have (e.g. GPA).

        Args:
            existing: The item already kept for this identity key
                (highest priority so far).
            incoming: A later, lower-priority item sharing the same
                identity key.

        Returns:
            ``existing`` unchanged if it had no blank fields fillable from
            ``incoming``, otherwise a new instance with the gaps filled.
        """
        if type(existing) is not type(incoming):
            return existing
        fill: dict[str, Any] = {}
        for field_name in type(existing).model_fields:
            current_value = getattr(existing, field_name)
            if current_value is not None and current_value != "":
                continue
            candidate_value = getattr(incoming, field_name)
            if candidate_value is not None and candidate_value != "":
                fill[field_name] = candidate_value
        if not fill:
            return existing
        return existing.model_copy(update=fill)


class ExperienceResolver(StructuredListResolver):
    """Resolves ``experiences``: identity-keyed by company/title/start_date."""

    item_type_name = "WorkExperience"


class EducationResolver(StructuredListResolver):
    """Resolves ``education``: identity-keyed by institution/degree."""

    item_type_name = "Education"


class CertificationResolver(StructuredListResolver):
    """Resolves ``certifications``: identity-keyed by name/issuer."""

    item_type_name = "Certification"
