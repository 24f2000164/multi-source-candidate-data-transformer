"""Public API for the transformer.confidence package.

Example::

    from transformer.confidence import (
        ConfidenceEngine,
        build_strategies,
        from_merge_report,
    )
"""

from transformer.confidence.aggregator import ConfidenceAggregator
from transformer.confidence.confidence_engine import ConfidenceEngine, build_strategies
from transformer.confidence.exceptions import ConfidenceError
from transformer.confidence.merge_metadata import (
    MergeMetadata,
    StaticMergeMetadata,
    from_merge_report,
    from_single_source,
)
from transformer.confidence.report import ConfidenceReport
from transformer.confidence.strategies import (
    AgreementStrategy,
    ConfidenceStrategy,
    ConflictPenaltyStrategy,
    MissingFieldStrategy,
    SourceWeightStrategy,
    StrategyContext,
    StrategyResult,
    TraceEntry,
)

__all__ = [
    "AgreementStrategy",
    "ConfidenceAggregator",
    "ConfidenceEngine",
    "ConfidenceError",
    "ConfidenceReport",
    "ConfidenceStrategy",
    "ConflictPenaltyStrategy",
    "MergeMetadata",
    "MissingFieldStrategy",
    "SourceWeightStrategy",
    "StaticMergeMetadata",
    "StrategyContext",
    "StrategyResult",
    "TraceEntry",
    "build_strategies",
    "from_merge_report",
    "from_single_source",
]
