"""Runs the config-defined strategy pipeline across fields and aggregates results."""

from transformer.confidence.merge_metadata import MergeMetadata
from transformer.confidence.strategies import (
    ConfidenceStrategy,
    StrategyContext,
    TraceEntry,
)
from transformer.models import Candidate, DataSource, FieldConfidence

_MIN_SCORE = 0.0
_MAX_SCORE = 1.0


class ConfidenceAggregator:
    """Aggregates the output of an ordered ``ConfidenceStrategy`` pipeline.

    Complexity: O(fields x strategies); each strategy itself runs in O(1)
    per field, so the overall pass is O(F) for a fixed strategy count.
    """

    def __init__(
        self,
        strategies: list[ConfidenceStrategy],
        *,
        field_weights: dict[str, float] | None = None,
        default_field_weight: float = 1.0,
    ) -> None:
        """Initialise the aggregator with an ordered strategy pipeline.

        Args:
            strategies: Strategies to run, in config-defined order. Order is
                meaningful (e.g. conflict penalty after agreement) and must
                be documented in ``confidence_rules.yaml``, not implied by
                code position.
            field_weights: Per-field weight used in the overall weighted
                average. Fields not present use ``default_field_weight``.
            default_field_weight: Weight used for fields without an explicit
                entry in ``field_weights``.
        """
        self._strategies = strategies
        self._field_weights = field_weights or {}
        self._default_field_weight = default_field_weight

    def aggregate(
        self,
        candidate: Candidate,
        metadata: MergeMetadata,
        field_names: list[str],
        source_weights: dict[DataSource, float],
    ) -> tuple[
        dict[str, FieldConfidence], float, tuple[TraceEntry, ...], list[str], list[str]
    ]:
        """Score every field in ``field_names`` and compute the overall score.

        Args:
            candidate: The candidate being scored.
            metadata: ``MergeMetadata`` view for this candidate.
            field_names: Canonical (dotted) field names to score.
            source_weights: Per-``DataSource`` base weight, from config.

        Returns:
            A tuple of ``(field_scores, overall_score, trace, penalties,
            bonuses)``. Fields whose value is absent (driven to score ``0``
            by the missing-field strategy) are excluded from the weighted
            average's denominator but still appear in ``field_scores``.
        """
        field_scores: dict[str, FieldConfidence] = {}
        trace: list[TraceEntry] = []
        penalties: list[str] = []
        bonuses: list[str] = []

        weighted_sum = 0.0
        weight_total = 0.0

        for field_name in field_names:
            running_score = 0.0
            field_excluded = False

            for strategy in self._strategies:
                context = StrategyContext(
                    candidate=candidate,
                    field_name=field_name,
                    merge_metadata=metadata,
                    source_weights=source_weights,
                    running_score=running_score,
                )
                result = strategy.score(context)
                old_score = running_score
                new_score = _clamp(running_score + result.delta)
                running_score = new_score

                trace.append(
                    TraceEntry(
                        field=field_name,
                        strategy=strategy.name,
                        old_score=old_score,
                        delta=result.delta,
                        new_score=new_score,
                        reason=result.reason,
                    )
                )

                if strategy.name == "missing_field" and result.delta < 0:
                    field_excluded = True
                    excluded_note = f"{field_name}: {result.reason}"
                    penalties.append(excluded_note)
                elif result.delta > 0:
                    bonuses.append(
                        f"{field_name}: {result.reason} (+{result.delta:.3f})"
                    )
                elif result.delta < 0:
                    penalties.append(
                        f"{field_name}: {result.reason} ({result.delta:.3f})"
                    )

            primary_source = _primary_source(metadata, field_name)
            field_scores[field_name] = FieldConfidence(
                score=running_score, source=primary_source
            )

            if not field_excluded:
                weight = self._field_weights.get(field_name, self._default_field_weight)
                weighted_sum += running_score * weight
                weight_total += weight

        overall = weighted_sum / weight_total if weight_total > 0 else 0.0
        overall = _clamp(overall)

        return field_scores, overall, tuple(trace), penalties, bonuses


def _clamp(value: float) -> float:
    """Clamp ``value`` to the closed range ``[0.0, 1.0]``.

    Args:
        value: Raw score value.

    Returns:
        The clamped score.
    """
    return max(_MIN_SCORE, min(_MAX_SCORE, value))


def _primary_source(metadata: MergeMetadata, field_name: str) -> DataSource:
    """Pick a representative source for a field's ``FieldConfidence`` record.

    Args:
        metadata: ``MergeMetadata`` view for the candidate.
        field_name: Canonical (dotted) field name.

    Returns:
        The first source considered for the field, or ``DataSource.ATS`` as
        a safe default when no sources are recorded (defensive fallback;
        should not occur for a properly built ``MergeMetadata``).
    """
    sources = metadata.sources_considered(field_name)
    return sources[0] if sources else DataSource.ATS
