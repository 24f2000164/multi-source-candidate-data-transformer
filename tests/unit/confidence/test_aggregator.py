"""Unit tests for transformer.confidence.aggregator.ConfidenceAggregator."""

from tests.unit.confidence._builders import make_candidate
from transformer.confidence.aggregator import ConfidenceAggregator
from transformer.confidence.merge_metadata import from_single_source
from transformer.confidence.strategies import (
    AgreementStrategy,
    ConflictPenaltyStrategy,
    MissingFieldStrategy,
    SourceWeightStrategy,
)
from transformer.models import DataSource

_SOURCE_WEIGHTS = {DataSource.ATS: 0.7, DataSource.RESUME: 0.6}


def _default_aggregator(**kwargs) -> ConfidenceAggregator:
    return ConfidenceAggregator(
        [
            SourceWeightStrategy(),
            AgreementStrategy(),
            ConflictPenaltyStrategy(),
            MissingFieldStrategy(),
        ],
        **kwargs,
    )


def test_trace_has_one_entry_per_field_per_strategy() -> None:
    candidate = make_candidate(skills=["python"])
    metadata = from_single_source(DataSource.ATS)
    aggregator = _default_aggregator()
    _, _, trace, _, _ = aggregator.aggregate(
        candidate, metadata, ["first_name", "skills"], _SOURCE_WEIGHTS
    )
    assert len(trace) == 2 * 4  # 2 fields x 4 strategies


def test_missing_optional_field_excluded_from_weighted_average() -> None:
    candidate = make_candidate(skills=[])
    metadata = from_single_source(DataSource.ATS)
    aggregator = _default_aggregator()
    field_scores, overall, _, _, _ = aggregator.aggregate(
        candidate, metadata, ["first_name", "skills"], _SOURCE_WEIGHTS
    )
    # skills is missing -> excluded from denominator -> overall equals
    # first_name's own score, not an average dragged down by skills' 0.
    assert field_scores["skills"].score == 0.0
    assert overall == field_scores["first_name"].score


def test_overall_score_is_zero_when_all_fields_missing() -> None:
    candidate = make_candidate(skills=[], first_name="X", last_name="Y")
    # Make every field "missing" by using empty metadata + blank candidate
    # fields where possible; first_name/last_name can't be blank (pydantic),
    # so verify the all-excluded path directly via skills + an unset contact.
    metadata = from_single_source(DataSource.ATS)
    aggregator = _default_aggregator()
    field_scores, overall, _, _, _ = aggregator.aggregate(
        candidate, metadata, ["skills", "contact"], _SOURCE_WEIGHTS
    )
    assert field_scores["skills"].score == 0.0
    assert field_scores["contact"].score == 0.0
    assert overall == 0.0


def test_field_weights_affect_overall_average() -> None:
    candidate = make_candidate(skills=["python"])
    metadata = from_single_source(DataSource.ATS)
    aggregator = _default_aggregator(
        field_weights={"first_name": 10.0, "skills": 0.0}
    )
    field_scores, overall, _, _, _ = aggregator.aggregate(
        candidate, metadata, ["first_name", "skills"], _SOURCE_WEIGHTS
    )
    # skills has weight 0 -> overall driven entirely by first_name.
    assert overall == field_scores["first_name"].score
