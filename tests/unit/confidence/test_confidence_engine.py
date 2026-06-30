"""Unit tests for transformer.confidence.confidence_engine.ConfidenceEngine."""

import pytest

from transformer.confidence.confidence_engine import ConfidenceEngine, build_strategies
from transformer.confidence.exceptions import ConfidenceError
from transformer.confidence.merge_metadata import from_single_source
from transformer.models import DataSource

from tests.unit.confidence._builders import make_candidate


def test_build_strategies_unknown_name_raises() -> None:
    with pytest.raises(ConfidenceError):
        build_strategies(["not_a_real_strategy"])


def test_build_strategies_known_names() -> None:
    strategies = build_strategies(
        ["source_weight", "agreement", "conflict_penalty", "missing_field"]
    )
    assert [s.name for s in strategies] == [
        "source_weight",
        "agreement",
        "conflict_penalty",
        "missing_field",
    ]


def test_engine_run_attaches_confidence_to_candidate() -> None:
    strategies = build_strategies(
        ["source_weight", "agreement", "conflict_penalty", "missing_field"]
    )
    engine = ConfidenceEngine(
        strategies=strategies,
        source_weights={DataSource.ATS: 0.7, DataSource.RESUME: 0.6},
        scored_fields=("first_name", "skills"),
        config_version="1.0",
    )
    candidate = make_candidate(skills=["python"])
    metadata = from_single_source(DataSource.ATS)

    scored, report = engine.run(candidate, metadata)

    assert scored.confidence is not None
    assert scored.confidence.score == report.overall_score
    assert report.config_version == "1.0"
    assert candidate.confidence is None  # original candidate untouched


def test_engine_does_not_mutate_input_candidate() -> None:
    strategies = build_strategies(["source_weight"])
    engine = ConfidenceEngine(
        strategies=strategies,
        source_weights={DataSource.ATS: 0.7},
        scored_fields=("first_name",),
    )
    candidate = make_candidate()
    engine.run(candidate, from_single_source(DataSource.ATS))
    assert candidate.confidence is None
