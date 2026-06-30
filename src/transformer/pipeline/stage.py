"""A minimal ``PipelineStage`` interface so Confidence/Validation (and future
stages, e.g. Projection) can be composed uniformly instead of the caller
hardcoding "run confidence, then run validation".
"""

from dataclasses import dataclass
from typing import Protocol

from transformer.confidence.confidence_engine import ConfidenceEngine
from transformer.confidence.merge_metadata import MergeMetadata
from transformer.models import Candidate
from transformer.validation.validation_engine import ValidationEngine


@dataclass(frozen=True)
class PipelineResult:
    """Accumulated output of running a sequence of ``PipelineStage``s.

    Attributes:
        candidate: The candidate after all stages have run.
        reports: Stage name -> report object, in execution order.
    """

    candidate: Candidate
    reports: dict[str, object]


class PipelineStage(Protocol):
    """A single named step in the confidence/validation pipeline."""

    name: str

    def run(self, candidate: Candidate, metadata: MergeMetadata
    ) -> tuple[Candidate, object]:
        """Run this stage.

        Args:
            candidate: Candidate as produced by the previous stage.
            metadata: ``MergeMetadata`` for the candidate (unused by stages
                that don't need it, e.g. a future ``ProjectionStage``).

        Returns:
            A tuple of ``(possibly-updated candidate, this stage's report)``.
        """
        ...


@dataclass(frozen=True)
class ConfidenceStage:
    """Wraps ``ConfidenceEngine`` as a ``PipelineStage``."""

    engine: ConfidenceEngine
    name: str = "confidence"

    def run(self, candidate: Candidate, metadata: MergeMetadata
            ) -> tuple[Candidate, object]:
        """Run confidence scoring.

        Args:
            candidate: Candidate to score.
            metadata: ``MergeMetadata`` for the candidate.

        Returns:
            ``(candidate_with_confidence, ConfidenceReport)``.
        """
        return self.engine.run(candidate, metadata)


@dataclass(frozen=True)
class ValidationStage:
    """Wraps ``ValidationEngine`` as a ``PipelineStage``."""

    engine: ValidationEngine
    name: str = "validation"

    def run(self, candidate: Candidate, metadata: MergeMetadata
            ) -> tuple[Candidate, object]:
        """Run validation.

        Args:
            candidate: Candidate to validate.
            metadata: Unused; present only to satisfy ``PipelineStage``.

        Returns:
            ``(candidate, ValidationReport)`` -- validation does not mutate
            the candidate.
        """
        return candidate, self.engine.run(candidate)


def run_pipeline(
    candidate: Candidate, metadata: MergeMetadata, stages: list[PipelineStage]
) -> PipelineResult:
    """Run a sequence of stages, threading the candidate through each.

    Args:
        candidate: Starting candidate (e.g. straight out of the merge engine).
        metadata: ``MergeMetadata`` made available to every stage.
        stages: Stages to run, in order, e.g.
            ``[ConfidenceStage(engine), ValidationStage(engine)]``.

    Returns:
        A ``PipelineResult`` with the final candidate and every stage's report.
    """
    reports: dict[str, object] = {}
    current = candidate
    for stage in stages:
        current, report = stage.run(current, metadata)
        reports[stage.name] = report
    return PipelineResult(candidate=current, reports=reports)
