"""Application facade for every supported candidate transformation use case."""

import json
import logging
from pathlib import Path

from transformer.application.result import ApplicationResult
from transformer.confidence.confidence_engine import ConfidenceEngine
from transformer.merge.merge_engine import MergeEngine
from transformer.models import Candidate
from transformer.normalizers.normalization_engine import NormalizationEngine
from transformer.parsers.ats_parser import ATSParser
from transformer.parsers.exceptions import InvalidJSONError, UnsupportedFormatError
from transformer.parsers.resume.resume_parser import ResumeParser
from transformer.pipeline.context import PipelineRequest, PipelineState
from transformer.pipeline.pipeline import Pipeline
from transformer.pipeline.stage import (
    ATSParserStage,
    ConfidenceStage,
    MergeStage,
    NormalizationStage,
    ProjectionStage,
    ResumeParserStage,
    StatePipelineStage,
    ValidationStage,
)
from transformer.projection.projection_engine import ProjectionEngine
from transformer.validation.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)

_ATS_SUFFIXES = frozenset({".json"})
_RESUME_SUFFIXES = frozenset({".pdf", ".docx"})


class ApplicationService:
    """Construct ordered stages and expose a single entry point per use case."""

    def __init__(
        self,
        *,
        pipeline: Pipeline,
        ats_parser: ATSParser,
        resume_parser: ResumeParser,
        normalization_engine: NormalizationEngine,
        merge_engine: MergeEngine,
        confidence_engine: ConfidenceEngine,
        validation_engine: ValidationEngine,
        projection_engine: ProjectionEngine,
    ) -> None:
        """Initialize the facade with all collaborators via constructor injection."""
        self._pipeline = pipeline
        self._ats_parser_stage = ATSParserStage(ats_parser)
        self._resume_parser_stage = ResumeParserStage(resume_parser)
        self._normalization_stage = NormalizationStage(normalization_engine)
        self._merge_stage = MergeStage(merge_engine)
        self._confidence_stage = ConfidenceStage(confidence_engine)
        self._validation_stage = ValidationStage(validation_engine)
        self._projection_stage = ProjectionStage(projection_engine)

    def parse(self, file_path: Path) -> ApplicationResult:
        """Run the complete single-source pipeline selected by file extension."""
        path = Path(file_path)
        self._ensure_exists(path)
        suffix = path.suffix.lower()
        if suffix in _ATS_SUFFIXES:
            request = PipelineRequest(ats_path=path, projection_format="canonical")
            parser_stage: StatePipelineStage = self._ats_parser_stage
        elif suffix in _RESUME_SUFFIXES:
            request = PipelineRequest(resume_path=path, projection_format="canonical")
            parser_stage = self._resume_parser_stage
        else:
            raise UnsupportedFormatError(
                f"unsupported input extension: {suffix or '(none)'}"
            )
        return self._execute(
            request,
            [
                parser_stage,
                self._normalization_stage,
                self._confidence_stage,
                self._validation_stage,
                self._projection_stage,
            ],
        )

    def merge(self, ats_path: Path, resume_path: Path) -> ApplicationResult:
        """Parse, normalize, and merge one ATS record with one resume."""
        self._ensure_exists(Path(ats_path))
        self._ensure_exists(Path(resume_path))
        request = PipelineRequest(
            ats_path=Path(ats_path), resume_path=Path(resume_path)
        )
        return self._execute(
            request,
            [
                self._ats_parser_stage,
                self._resume_parser_stage,
                self._normalization_stage,
                self._merge_stage,
            ],
        )

    def validate(self, candidate_path: Path) -> ApplicationResult:
        """Load canonical candidate JSON and run validation only."""
        path = Path(candidate_path)
        request = PipelineRequest(candidate_path=path)
        state = PipelineState(merged_candidate=self._load_candidate(path))
        return self._execute(request, [self._validation_stage], state)

    def project(self, candidate_path: Path, format_name: str) -> ApplicationResult:
        """Load canonical candidate JSON and run one named projection."""
        path = Path(candidate_path)
        request = PipelineRequest(candidate_path=path, projection_format=format_name)
        state = PipelineState(merged_candidate=self._load_candidate(path))
        return self._execute(request, [self._projection_stage], state)

    def transform(
        self,
        ats_path: Path,
        resume_path: Path,
        format_name: str = "canonical",
    ) -> ApplicationResult:
        """Run the complete ATS-plus-resume transformation pipeline."""
        self._ensure_exists(Path(ats_path))
        self._ensure_exists(Path(resume_path))
        request = PipelineRequest(
            ats_path=Path(ats_path),
            resume_path=Path(resume_path),
            projection_format=format_name,
        )
        return self._execute(
            request,
            [
                self._ats_parser_stage,
                self._resume_parser_stage,
                self._normalization_stage,
                self._merge_stage,
                self._confidence_stage,
                self._validation_stage,
                self._projection_stage,
            ],
        )

    def _execute(
        self,
        request: PipelineRequest,
        stages: list[StatePipelineStage],
        state: PipelineState | None = None,
    ) -> ApplicationResult:
        logger.info("pipeline_started", extra={"stages": [s.name for s in stages]})
        completed = self._pipeline.execute(request, stages, state)
        validation_report = completed.reports.get("validation")
        success = bool(getattr(validation_report, "is_valid", True))
        logger.info("pipeline_completed", extra={"success": success})
        return ApplicationResult(
            candidate=completed.merged_candidate,
            projection=completed.projection,
            reports=dict(completed.reports),
            warnings=list(completed.warnings),
            success=success,
            exit_code=0 if success else 1,
        )

    @staticmethod
    def _load_candidate(path: Path) -> Candidate:
        """Read strict canonical candidate JSON from disk."""
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            if not path.exists():
                raise FileNotFoundError(path) from exc
            raise
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise InvalidJSONError(
                f"file does not contain valid JSON: {path.name}"
            ) from exc
        payload = data.get("candidate", data)
        return Candidate.model_validate(payload)

    @staticmethod
    def _ensure_exists(path: Path) -> None:
        """Raise the standard path-aware exception for a missing input file."""
        if not path.exists():
            raise FileNotFoundError(path)
