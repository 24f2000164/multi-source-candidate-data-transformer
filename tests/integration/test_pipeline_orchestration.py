"""Pipeline ordering, conflict, warning, and statelessness integration tests."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from transformer.application import ApplicationService
from transformer.merge.merge_engine import MergeEngine
from transformer.merge.report import MergeReport
from transformer.models import Candidate, DataSource, FieldProvenance
from transformer.pipeline.context import PipelineRequest, PipelineState
from transformer.pipeline.pipeline import Pipeline
from transformer.projection.exceptions import UnknownProjectionTypeError


def _candidate(source: DataSource, first_name: str) -> Candidate:
    provenance = {
        "first_name": FieldProvenance(
            source=source,
            raw_value=first_name,
            extracted_at=datetime.now(UTC),
        ),
        "last_name": FieldProvenance(
            source=source,
            raw_value="Doe",
            extracted_at=datetime.now(UTC),
        ),
    }
    return Candidate(first_name=first_name, last_name="Doe", provenance=provenance)


class _Parser:
    def __init__(self, candidate: Candidate) -> None:
        self.candidate = candidate
        self.calls = 0

    def parse(self, source: Path) -> Candidate:
        del source
        self.calls += 1
        return self.candidate


class _Normalizer:
    def normalize(self, candidate: Candidate) -> Candidate:
        return candidate


@dataclass(frozen=True)
class _Report:
    warnings: tuple[str, ...] = ()
    is_valid: bool = True


class _Confidence:
    def run(self, candidate: Candidate, metadata: object) -> tuple[Candidate, _Report]:
        del metadata
        return candidate, _Report()


class _Validation:
    def run(self, candidate: Candidate) -> _Report:
        del candidate
        return _Report()


class _Projection:
    def project(
        self, candidate: Candidate, name: str
    ) -> tuple[dict[str, object], _Report]:
        if name == "unknown":
            raise UnknownProjectionTypeError("unknown projection type: 'unknown'")
        return candidate.model_dump(mode="json"), _Report()


def _service(ats: _Parser, resume: _Parser) -> ApplicationService:
    return ApplicationService(
        pipeline=Pipeline(),
        ats_parser=ats,  # type: ignore[arg-type]
        resume_parser=resume,  # type: ignore[arg-type]
        normalization_engine=_Normalizer(),  # type: ignore[arg-type]
        merge_engine=MergeEngine(),
        confidence_engine=_Confidence(),  # type: ignore[arg-type]
        validation_engine=_Validation(),  # type: ignore[arg-type]
        projection_engine=_Projection(),  # type: ignore[arg-type]
    )


def test_merge_conflict_is_reported_and_parsers_run_once(tmp_path: Path) -> None:
    ats = _Parser(_candidate(DataSource.ATS, "Jane"))
    resume = _Parser(_candidate(DataSource.RESUME, "Janet"))
    ats_path = tmp_path / "candidate.json"
    resume_path = tmp_path / "resume.pdf"
    ats_path.write_text("{}", encoding="utf-8")
    resume_path.write_bytes(b"stub")

    result = _service(ats, resume).transform(ats_path, resume_path)

    merge_report = result.reports["merge"]
    assert isinstance(merge_report, MergeReport)
    assert merge_report.conflicts
    assert ats.calls == 1
    assert resume.calls == 1
    assert result.warnings


@dataclass(frozen=True)
class _OrderedStage:
    name: str
    calls: list[str]

    def execute(self, request: PipelineRequest, state: PipelineState) -> _Report:
        del request, state
        self.calls.append(self.name)
        return _Report()


def test_pipeline_obeys_caller_order_and_has_no_cross_run_state() -> None:
    calls: list[str] = []
    stages = [_OrderedStage("second", calls), _OrderedStage("first", calls)]
    pipeline = Pipeline()

    first = pipeline.execute(PipelineRequest(), stages)
    second = pipeline.execute(PipelineRequest(), [])

    assert calls == ["second", "first"]
    assert list(first.reports) == ["second", "first"]
    assert second.reports == {}
    assert first is not second
