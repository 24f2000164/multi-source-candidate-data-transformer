"""``ConfidenceEngine``: the orchestrator wired up by the pipeline/CLI."""

from transformer.confidence.aggregator import ConfidenceAggregator
from transformer.confidence.exceptions import ConfidenceError
from transformer.confidence.merge_metadata import MergeMetadata
from transformer.confidence.report import ConfidenceReport
from transformer.confidence.strategies import (
    AgreementStrategy,
    ConfidenceStrategy,
    ConflictPenaltyStrategy,
    MissingFieldStrategy,
    SourceWeightStrategy,
)
from transformer.models import Candidate, DataSource, OverallConfidence

# Default scored fields when the candidate-specific field list isn't
# supplied by the caller. Kept narrow and explicit rather than reflecting
# over every model attribute, since not all attributes are meaningfully
# "confidence scored" (e.g. `id`, `schema_version`).
DEFAULT_SCORED_FIELDS: tuple[str, ...] = (
    "first_name",
    "last_name",
    "contact",
    "experiences",
    "education",
    "skills",
)

_STRATEGY_REGISTRY: dict[str, type] = {
    "source_weight": SourceWeightStrategy,
    "agreement": AgreementStrategy,
    "conflict_penalty": ConflictPenaltyStrategy,
    "missing_field": MissingFieldStrategy,
}


def build_strategies(strategy_names: list[str]) -> list[ConfidenceStrategy]:
    """Instantiate strategies from their config-declared names, in order.

    Args:
        strategy_names: Strategy names in the order they should execute,
            e.g. ``["source_weight", "agreement", "conflict_penalty",
            "missing_field"]``.

    Returns:
        Instantiated strategies in the given order.

    Raises:
        ConfidenceError: If a name is not a recognised strategy.
    """
    strategies: list[ConfidenceStrategy] = []
    for name in strategy_names:
        strategy_cls = _STRATEGY_REGISTRY.get(name)
        if strategy_cls is None:
            raise ConfidenceError(f"unknown confidence strategy: {name!r}")
        strategies.append(strategy_cls())
    return strategies


class ConfidenceEngine:
    """Scores a ``Candidate`` and produces a ``ConfidenceReport``.

    Constructor-injected with everything it needs: an ordered strategy
    pipeline, source weights, optional per-field weights, and a config
    version string for the report -- all sourced from a ``Config`` object
    produced by ``ConfigLoader``, never read by the engine itself.
    """

    def __init__(
        self,
        *,
        strategies: list[ConfidenceStrategy],
        source_weights: dict[DataSource, float],
        field_weights: dict[str, float] | None = None,
        scored_fields: tuple[str, ...] = DEFAULT_SCORED_FIELDS,
        config_version: str = "",
    ) -> None:
        """Initialise the engine with its full configuration.

        Args:
            strategies: Ordered strategy pipeline.
            source_weights: Per-``DataSource`` base weight.
            field_weights: Optional per-field weight for the overall average.
            scored_fields: Canonical (dotted) field names to score.
            config_version: Version string recorded in the resulting report.
        """
        self._aggregator = ConfidenceAggregator(strategies, field_weights=field_weights)
        self._source_weights = source_weights
        self._scored_fields = list(scored_fields)
        self._config_version = config_version

    def run(
        self, candidate: Candidate, metadata: MergeMetadata
    ) -> tuple[Candidate, ConfidenceReport]:
        """Score ``candidate`` and attach the resulting ``OverallConfidence``.

        Args:
            candidate: Candidate to score (not mutated; a new instance with
                ``confidence`` populated is returned, since ``Candidate`` is
                frozen).
            metadata: ``MergeMetadata`` view for this candidate.

        Returns:
            A tuple of ``(candidate_with_confidence, confidence_report)``.
        """
        field_scores, overall_score, trace, penalties, bonuses = (
            self._aggregator.aggregate(
                candidate, metadata, self._scored_fields, self._source_weights
            )
        )

        report = ConfidenceReport(
            field_scores=field_scores,
            overall_score=overall_score,
            calculation_trace=trace,
            source_weights=dict(self._source_weights),
            penalties=tuple(penalties),
            bonuses=tuple(bonuses),
            config_version=self._config_version,
        )

        overall = OverallConfidence(score=overall_score, fields=field_scores)
        scored_candidate = candidate.model_copy(update={"confidence": overall})

        return scored_candidate, report
