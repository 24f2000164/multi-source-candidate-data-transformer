"""Confidence scoring strategies.

Each ``ConfidenceStrategy`` is independent: it reads ``StrategyContext`` and
the running score so far, and returns a ``StrategyResult`` carrying only a
*delta* and a human-readable *reason*. A strategy must never reach into, or
depend on, the output of another strategy -- the aggregator is solely
responsible for combining deltas in config-defined order. This keeps
strategy ordering a pure aggregation concern (documented in
``config/confidence_rules.yaml``) rather than an implicit code dependency.
"""

import math
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from transformer.confidence.merge_metadata import MergeMetadata
from transformer.models import Candidate, DataSource


@dataclass(frozen=True)
class StrategyContext:
    """Read-only context made available to every confidence strategy.

    Attributes:
        candidate: The full candidate record being scored (read-only; a
            strategy may inspect any field, not just the one it scores).
        field_name: Canonical (dotted) name of the field being scored.
        merge_metadata: ``MergeMetadata`` view for this candidate.
        source_weights: Per-``DataSource`` base weight, from config.
        running_score: The field's accumulated score *before* this
            strategy's delta is applied -- read-only, informational; a
            strategy must not assume any particular prior contributor ran.
    """

    candidate: Candidate
    field_name: str
    merge_metadata: MergeMetadata
    source_weights: dict[DataSource, float]
    running_score: float


@dataclass(frozen=True)
class StrategyResult:
    """The output of a single strategy for a single field.

    Attributes:
        delta: Signed contribution to the field's score. Strategies never
            return an absolute score -- only a delta.
        reason: Short human-readable explanation, recorded in the trace.
    """

    delta: float
    reason: str


@dataclass(frozen=True)
class TraceEntry:
    """One row of the confidence calculation trace.

    Attributes:
        field: Canonical (dotted) field name.
        strategy: Name of the strategy that produced this entry.
        old_score: Field score before this strategy ran.
        delta: Signed contribution applied by this strategy.
        new_score: Field score after this strategy ran (``old_score + delta``,
            clamped to ``[0.0, 1.0]`` by the aggregator).
        reason: Human-readable explanation from the strategy.
    """

    field: str
    strategy: str
    old_score: float
    delta: float
    new_score: float
    reason: str


@runtime_checkable
class ConfidenceStrategy(Protocol):
    """A single, independent contributor to a field's confidence score."""

    name: str

    def score(self, context: StrategyContext) -> StrategyResult:
        """Compute this strategy's delta contribution for one field.

        Args:
            context: Read-only scoring context.

        Returns:
            A ``StrategyResult`` with a delta and reason. Must never raise
            for missing/partial data -- degrade to a zero delta instead.
        """
        ...


def _field_value(candidate: Candidate, field_name: str) -> object:
    """Resolve a dotted canonical field name to a value on ``candidate``.

    Args:
        candidate: The candidate record.
        field_name: Dotted field name, e.g. ``"contact.email"``.

    Returns:
        The resolved value, or ``None`` if any segment is missing/unresolvable.
    """
    value: object = candidate
    for part in field_name.split("."):
        if value is None:
            return None
        value = getattr(value, part, None)
    return value


class SourceWeightStrategy:
    """Seeds the field score from the per-``DataSource`` base weight in config."""

    name = "source_weight"

    def score(self, context: StrategyContext) -> StrategyResult:
        """Return the configured base weight of the field's primary source.

        Args:
            context: Read-only scoring context.

        Returns:
            Delta equal to the highest weight among sources considered for
            this field (``0.0`` if no sources were considered).
        """
        sources = context.merge_metadata.sources_considered(context.field_name)
        if not sources:
            return StrategyResult(delta=0.0, reason="no sources considered")
        weight = max(context.source_weights.get(s, 0.0) for s in sources)
        return StrategyResult(
            delta=weight,
            reason=f"base weight from sources {tuple(s.value for s in sources)}",
        )


class AgreementStrategy:
    """Rewards fields where multiple sources independently agreed."""

    name = "agreement"

    def __init__(self, *, bonus: float = 0.1) -> None:
        """Initialise with the bonus applied when sources agree.

        Args:
            bonus: Delta applied when more than one source contributed and
                no conflict was recorded.
        """
        self._bonus = bonus

    def score(self, context: StrategyContext) -> StrategyResult:
        """Apply the agreement bonus when applicable.

        Args:
            context: Read-only scoring context.

        Returns:
            ``+bonus`` if more than one source contributed without conflict,
            otherwise ``0.0``.
        """
        count = context.merge_metadata.contributing_source_count(context.field_name)
        conflict = context.merge_metadata.field_conflict(context.field_name)
        if count > 1 and not conflict:
            return StrategyResult(
                delta=self._bonus,
                reason=f"{count} sources agreed",
            )
        return StrategyResult(delta=0.0, reason="no multi-source agreement")


class ConflictPenaltyStrategy:
    """Penalises fields where sources disagreed during merge."""

    name = "conflict_penalty"

    def __init__(self, *, penalty: float = 0.2) -> None:
        """Initialise with the penalty applied on conflict.

        Args:
            penalty: Magnitude subtracted when ``field_conflict`` is true.
        """
        self._penalty = penalty

    def score(self, context: StrategyContext) -> StrategyResult:
        """Apply the conflict penalty when applicable.

        Args:
            context: Read-only scoring context.

        Returns:
            ``-penalty`` if sources conflicted, otherwise ``0.0``.
        """
        if context.merge_metadata.field_conflict(context.field_name):
            return StrategyResult(
                delta=-self._penalty,
                reason="sources disagreed on this field",
            )
        return StrategyResult(delta=0.0, reason="no conflict")


class MissingFieldStrategy:
    """Zeroes out / excludes scoring for absent optional fields."""

    name = "missing_field"

    def score(self, context: StrategyContext) -> StrategyResult:
        """Return a large negative delta when the field value is absent.

        The aggregator is responsible for excluding such fields from the
        weighted-average denominator; this strategy only signals "absent" by
        driving the score to ``0`` regardless of prior deltas.

        Args:
            context: Read-only scoring context.

        Returns:
            A delta that zeroes the running score when the value is missing
            (empty string, ``None``, or empty collection), else ``0.0``.
        """
        value = _field_value(context.candidate, context.field_name)
        is_missing = value is None or value == "" or value == []
        if is_missing:
            return StrategyResult(
                delta=-context.running_score,
                reason="field value is absent",
            )
        return StrategyResult(delta=0.0, reason="field value present")


def is_finite_score(value: float) -> bool:
    """Return whether ``value`` is a finite (non-NaN, non-infinite) number.

    Args:
        value: The number to check.

    Returns:
        ``True`` if ``value`` is finite.
    """
    return math.isfinite(value)
