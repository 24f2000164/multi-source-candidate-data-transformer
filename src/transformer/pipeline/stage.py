"""A minimal ``PipelineStage`` interface so Confidence/Validation (and future
stages, e.g. Projection) can be composed uniformly instead of the caller
hardcoding "run confidence, then run validation".
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from transformer.confidence.confidence_engine import ConfidenceEngine
from transformer.confidence.merge_metadata import (
    MergeMetadata,
    from_merge_report,
    from_single_source,
)
from transformer.merge.merge_engine import MergeEngine
from transformer.models import Candidate, DataSource
from transformer.normalizers.normalization_engine import NormalizationEngine
from transformer.parsers.ats_parser import ATSParser
from transformer.parsers.resume.resume_parser import ResumeParser
from transformer.pipeline.context import PipelineRequest, PipelineState
from transformer.projection.projection_engine import ProjectionEngine
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

    def run(
        self, candidate: Candidate, metadata: MergeMetadata
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


class StatePipelineStage(Protocol):
    """A stage operating on the approved request/state orchestration contract."""

    @property
    def name(self) -> str:
        """Return the stable report key for this stage."""
        ...

    def execute(self, request: PipelineRequest, state: PipelineState) -> object | None:
        """Execute against one request and its current mutable state."""
        ...


@dataclass(frozen=True)
class ParserStageReport:
    """Minimal audit information for a successful parser stage."""

    source: DataSource
    path: Path
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class NormalizationReport:
    """Records which source candidates were normalized."""

    sources: tuple[DataSource, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ATSParserStage:
    """Parse the ATS input from a request into pipeline state."""

    parser: ATSParser
    name: str = "ats_parser"

    def execute(
        self, request: PipelineRequest, state: PipelineState
    ) -> ParserStageReport:
        """Parse the configured ATS path exactly once."""
        if request.ats_path is None:
            raise RuntimeError("ATS parser stage requires an ATS path")
        state.ats_candidate = self.parser.parse(request.ats_path)
        return ParserStageReport(DataSource.ATS, request.ats_path)


@dataclass(frozen=True)
class ResumeParserStage:
    """Parse the resume input from a request into pipeline state."""

    parser: ResumeParser
    name: str = "resume_parser"

    def execute(
        self, request: PipelineRequest, state: PipelineState
    ) -> ParserStageReport:
        """Parse the configured resume path exactly once."""
        if request.resume_path is None:
            raise RuntimeError("resume parser stage requires a resume path")
        state.resume_candidate = self.parser.parse(request.resume_path)
        return ParserStageReport(DataSource.RESUME, request.resume_path)


@dataclass(frozen=True)
class NormalizationStage:
    """Normalize every source candidate currently present in state."""

    engine: NormalizationEngine
    name: str = "normalization"

    def execute(
        self, request: PipelineRequest, state: PipelineState
    ) -> NormalizationReport:
        """Normalize each parsed source once, before an optional merge."""
        del request
        sources: list[DataSource] = []
        if state.ats_candidate is not None:
            state.ats_candidate = self.engine.normalize(state.ats_candidate)
            sources.append(DataSource.ATS)
        if state.resume_candidate is not None:
            state.resume_candidate = self.engine.normalize(state.resume_candidate)
            sources.append(DataSource.RESUME)
        if len(sources) == 1:
            state.merged_candidate = (
                state.ats_candidate
                if state.ats_candidate is not None
                else state.resume_candidate
            )
        if not sources:
            raise RuntimeError("normalization stage requires a parsed candidate")
        return NormalizationReport(tuple(sources))


@dataclass(frozen=True)
class MergeStage:
    """Merge normalized ATS and resume candidates."""

    engine: MergeEngine
    name: str = "merge"

    def execute(self, request: PipelineRequest, state: PipelineState) -> object:
        """Merge both source candidates and retain confidence metadata."""
        del request
        candidates = [
            candidate
            for candidate in (state.ats_candidate, state.resume_candidate)
            if candidate is not None
        ]
        merged, report = self.engine.merge(candidates)
        state.merged_candidate = merged
        state.merge_metadata = from_merge_report(report)
        return report


@dataclass(frozen=True)
class ConfidenceStage:
    """Wraps ``ConfidenceEngine`` as a ``PipelineStage``."""

    engine: ConfidenceEngine
    name: str = "confidence"

    def run(
        self, candidate: Candidate, metadata: MergeMetadata
    ) -> tuple[Candidate, object]:
        """Run confidence scoring.

        Args:
            candidate: Candidate to score.
            metadata: ``MergeMetadata`` for the candidate.

        Returns:
            ``(candidate_with_confidence, ConfidenceReport)``.
        """
        return self.engine.run(candidate, metadata)

    def execute(self, request: PipelineRequest, state: PipelineState) -> object:
        """Score the current candidate using merge or single-source metadata."""
        del request
        metadata = state.merge_metadata
        if metadata is None:
            if state.ats_candidate is not None and state.resume_candidate is None:
                metadata = from_single_source(DataSource.ATS)
            elif state.resume_candidate is not None and state.ats_candidate is None:
                metadata = from_single_source(DataSource.RESUME)
            else:
                raise RuntimeError("confidence stage requires source metadata")
        candidate, report = self.engine.run(state.require_candidate(), metadata)
        state.merged_candidate = candidate
        state.merge_metadata = metadata
        return report


@dataclass(frozen=True)
class ValidationStage:
    """Wraps ``ValidationEngine`` as a ``PipelineStage``."""

    engine: ValidationEngine
    name: str = "validation"

    def run(
        self, candidate: Candidate, metadata: MergeMetadata
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

    def execute(self, request: PipelineRequest, state: PipelineState) -> object:
        """Validate the current candidate without treating issues as exceptions."""
        del request
        return self.engine.run(state.require_candidate())


@dataclass(frozen=True)
class ProjectionStage:
    """Project the current candidate into the requested output shape."""

    engine: ProjectionEngine
    name: str = "projection"

    def execute(self, request: PipelineRequest, state: PipelineState) -> object:
        """Project and retain the JSON-safe payload in pipeline state."""
        projection_format = request.projection_format or "canonical"
        projection, report = self.engine.project(
            state.require_candidate(), projection_format
        )
        state.projection = projection
        return report


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
