"""Reusable, field-agnostic merge strategies.

Each strategy implements a single, narrow responsibility (Strategy
pattern), so resolvers compose behaviour instead of hardcoding
field-specific conditionals. Strategies operate on ``SourceValue`` --
a single field's value tagged with the source that produced it -- and never
know which canonical field they are resolving.
"""

from dataclasses import dataclass
from typing import Any, Protocol

from transformer.models import DataSource


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, list, dict, tuple, set)):
        return len(value) == 0
    return False


@dataclass(frozen=True)
class SourceValue:
    """A single field value tagged with provenance metadata.

    Attributes:
        source: The ``DataSource`` that produced this value.
        value: The (already-normalized) field value.
        confidence: Optional confidence score in ``[0.0, 1.0]`` used by
            ``HighestConfidenceStrategy``.
    """

    source: DataSource
    value: Any
    confidence: float | None = None


@dataclass(frozen=True)
class StrategyResult:
    """The outcome of applying a strategy to a set of ``SourceValue``s.

    Attributes:
        value: The chosen value (``None`` if no source provided one).
        winning_source: The source the chosen value came from, if any.
        contributing_sources: All sources whose non-empty value fed into
            the result (for ``union``-style strategies this may be more
            than one; for selection strategies it is at most one).
        conflict: ``True`` if multiple sources provided differing non-empty
            values and a choice had to be made between them.
    """

    value: Any
    winning_source: DataSource | None
    contributing_sources: tuple[DataSource, ...]
    conflict: bool


class MergeStrategy(Protocol):
    """Common interface every merge strategy implements."""

    name: str

    def apply(
        self, values: list[SourceValue], priority: tuple[DataSource, ...]
    ) -> StrategyResult:
        """Resolve a winning value from a set of per-source values.

        Args:
            values: Non-empty-or-empty candidate values, one per source
                that attempted to supply this field.
            priority: Source priority order, highest priority first.

        Returns:
            The resolution outcome.
        """
        ...


def _ordered_non_empty(
    values: list[SourceValue], priority: tuple[DataSource, ...]
) -> list[SourceValue]:
    non_empty = [v for v in values if not _is_empty(v.value)]

    def _rank(value: SourceValue) -> int:
        return (
            priority.index(value.source) if value.source in priority else len(priority)
        )

    # Stable sort: entries sharing a source (e.g. two RESUME candidates in an
    # N-source merge) keep their relative input order instead of being
    # collapsed, so no source's data is silently dropped.
    return sorted(non_empty, key=_rank)


class SourcePriorityStrategy:
    """Pick the highest-priority non-empty value; flag disagreement."""

    name = "source_priority"

    def apply(
        self, values: list[SourceValue], priority: tuple[DataSource, ...]
    ) -> StrategyResult:
        ordered = _ordered_non_empty(values, priority)
        if not ordered:
            return StrategyResult(None, None, (), False)
        winner = ordered[0]
        distinct_values = {repr(v.value) for v in ordered}
        conflict = len(distinct_values) > 1
        return StrategyResult(
            value=winner.value,
            winning_source=winner.source,
            contributing_sources=tuple(v.source for v in ordered),
            conflict=conflict,
        )


class FirstNonEmptyStrategy:
    """Pick the first non-empty value in priority order, no conflict flag."""

    name = "first_non_empty"

    def apply(
        self, values: list[SourceValue], priority: tuple[DataSource, ...]
    ) -> StrategyResult:
        ordered = _ordered_non_empty(values, priority)
        if not ordered:
            return StrategyResult(None, None, (), False)
        winner = ordered[0]
        return StrategyResult(
            value=winner.value,
            winning_source=winner.source,
            contributing_sources=(winner.source,),
            conflict=False,
        )


class HighestConfidenceStrategy:
    """Pick the value with the highest confidence score.

    Falls back to ``SourcePriorityStrategy`` when no value carries a
    confidence score (e.g. the confidence engine has not run yet).
    """

    name = "highest_confidence"

    def __init__(self) -> None:
        self._fallback = SourcePriorityStrategy()

    def apply(
        self, values: list[SourceValue], priority: tuple[DataSource, ...]
    ) -> StrategyResult:
        ordered = _ordered_non_empty(values, priority)
        scored = [v for v in ordered if v.confidence is not None]
        if not scored:
            return self._fallback.apply(values, priority)
        winner = max(
            scored,
            key=lambda v: (
                (v.confidence, -priority.index(v.source))
                if v.source in priority
                else (v.confidence, -len(priority))
            ),
        )
        distinct_values = {repr(v.value) for v in ordered}
        return StrategyResult(
            value=winner.value,
            winning_source=winner.source,
            contributing_sources=tuple(v.source for v in ordered),
            conflict=len(distinct_values) > 1,
        )


class UnionStrategy:
    """Union-merge values together; caller supplies the merge function.

    Used for both flat lists (case-insensitive string dedup) and
    identity-keyed structured lists -- the actual merging logic lives in
    ``merge_fn`` so this strategy stays generic.
    """

    name = "union"

    def __init__(self, merge_fn: Any) -> None:
        """Initialise with a list-merging function.

        Args:
            merge_fn: Callable ``(list[SourceValue]) -> list[Any]`` that
                merges the non-empty values from every contributing source.
        """
        self._merge_fn = merge_fn

    def apply(
        self, values: list[SourceValue], priority: tuple[DataSource, ...]
    ) -> StrategyResult:
        ordered = _ordered_non_empty(values, priority)
        if not ordered:
            return StrategyResult([], None, (), False)
        merged = self._merge_fn(ordered)
        return StrategyResult(
            value=merged,
            winning_source=None,
            contributing_sources=tuple(v.source for v in ordered),
            conflict=False,
        )
