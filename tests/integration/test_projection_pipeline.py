"""Integration tests: Candidate -> ProjectionEngine -> JSON-serializable dict."""

import json

import pytest

from transformer.projection import (
    AssignmentProjection,
    CanonicalProjection,
    ProjectionEngine,
    ProjectionRegistry,
    UnknownProjectionTypeError,
)
from tests.unit.projection._builders import full_candidate, make_candidate


def _build_engine() -> ProjectionEngine:
    registry = ProjectionRegistry(
        {
            "canonical": CanonicalProjection(),
            "assignment": AssignmentProjection(),
        }
    )
    return ProjectionEngine(registry)


class TestProjectionPipeline:
    def test_canonical_projection_round_trips_to_json(self) -> None:
        engine = _build_engine()
        candidate = full_candidate()

        output, report = engine.project(candidate, "canonical")

        assert json.loads(json.dumps(output))
        assert report.projection_type == "canonical"
        assert report.field_count == len(output)

    def test_assignment_projection_round_trips_to_json(self) -> None:
        engine = _build_engine()
        candidate = full_candidate()

        output, report = engine.project(candidate, "assignment")

        assert json.loads(json.dumps(output))
        assert output["firstName"] == "Jane"
        assert report.projection_type == "assignment"

    def test_unknown_projection_type(self) -> None:
        engine = _build_engine()

        with pytest.raises(UnknownProjectionTypeError):
            engine.project(make_candidate(), "unknown")

    def test_empty_candidate_minimal_required_fields(self) -> None:
        engine = _build_engine()
        candidate = make_candidate(external_id=None)

        canonical_output, _ = engine.project(candidate, "canonical")
        assignment_output, _ = engine.project(candidate, "assignment")

        assert canonical_output["experiences"] == []
        assert "email" not in assignment_output

    def test_unicode_candidate(self) -> None:
        engine = _build_engine()
        candidate = make_candidate(first_name="日本語", last_name="Søren")

        output, _ = engine.project(candidate, "canonical")

        assert output["first_name"] == "日本語"
        assert json.dumps(output, ensure_ascii=False)

    def test_idempotency_across_projection_types(self) -> None:
        engine = _build_engine()
        candidate = full_candidate()

        for projection_type in ("canonical", "assignment"):
            first, _ = engine.project(candidate, projection_type)
            second, _ = engine.project(candidate, projection_type)
            assert first == second
