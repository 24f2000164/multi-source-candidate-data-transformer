"""Unit tests for ``ProjectionEngine``."""

import pytest

from transformer.projection.canonical_projection import CanonicalProjection
from transformer.projection.exceptions import UnknownProjectionTypeError
from transformer.projection.projection_engine import ProjectionEngine
from transformer.projection.projection_registry import ProjectionRegistry
from tests.unit.projection._builders import full_candidate, make_candidate


class TestProjectionEngine:
    def test_project_returns_output_and_report(self) -> None:
        registry = ProjectionRegistry({"canonical": CanonicalProjection()})
        engine = ProjectionEngine(registry)
        candidate = full_candidate()

        output, report = engine.project(candidate, "canonical")

        assert output["first_name"] == "Jane"
        assert report.projection_type == "canonical"
        assert report.field_count == len(output)
        assert report.warnings == ()

    def test_report_has_no_output_field(self) -> None:
        registry = ProjectionRegistry({"canonical": CanonicalProjection()})
        engine = ProjectionEngine(registry)
        _, report = engine.project(full_candidate(), "canonical")

        assert not hasattr(report, "output")

    def test_unknown_projection_type_raises(self) -> None:
        registry = ProjectionRegistry({"canonical": CanonicalProjection()})
        engine = ProjectionEngine(registry)

        with pytest.raises(UnknownProjectionTypeError):
            engine.project(make_candidate(), "nonexistent")

    def test_field_count_matches_minimal_candidate(self) -> None:
        registry = ProjectionRegistry({"canonical": CanonicalProjection()})
        engine = ProjectionEngine(registry)
        output, report = engine.project(make_candidate(), "canonical")

        assert report.field_count == len(output)

    def test_idempotent_projection(self) -> None:
        registry = ProjectionRegistry({"canonical": CanonicalProjection()})
        engine = ProjectionEngine(registry)
        candidate = full_candidate()

        output_1, _ = engine.project(candidate, "canonical")
        output_2, _ = engine.project(candidate, "canonical")

        assert output_1 == output_2
