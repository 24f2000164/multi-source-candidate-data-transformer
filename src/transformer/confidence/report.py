"""The ``ConfidenceReport`` produced by every confidence-engine run."""

from pydantic import BaseModel, ConfigDict, Field

from transformer.confidence.strategies import TraceEntry
from transformer.models import DataSource, FieldConfidence


class ConfidenceReport(BaseModel):
    """Full audit trail and result of one confidence-scoring run.

    Attributes:
        field_scores: Final per-field confidence, keyed by canonical
            (dotted) field name.
        overall_score: Weighted-average confidence across scored fields.
        calculation_trace: Per-field, per-strategy delta/reason entries, in
            the order strategies executed.
        source_weights: The per-``DataSource`` base weights used, from config.
        penalties: Human-readable notes for every penalty applied.
        bonuses: Human-readable notes for every bonus applied.
        config_version: Version of ``confidence_rules.yaml`` used.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    field_scores: dict[str, FieldConfidence] = Field(default_factory=dict)
    overall_score: float = Field(..., ge=0.0, le=1.0)
    calculation_trace: tuple[TraceEntry, ...] = ()
    source_weights: dict[DataSource, float] = Field(default_factory=dict)
    penalties: tuple[str, ...] = ()
    bonuses: tuple[str, ...] = ()
    config_version: str = ""
