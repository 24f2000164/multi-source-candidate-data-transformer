"""Unit tests for transformer.confidence.strategies."""

from transformer.confidence.merge_metadata import StaticMergeMetadata, _FieldMergeView
from transformer.confidence.strategies import (
    AgreementStrategy,
    ConflictPenaltyStrategy,
    MissingFieldStrategy,
    SourceWeightStrategy,
    StrategyContext,
)
from transformer.models import DataSource

from tests.unit.confidence._builders import make_candidate


def _metadata(**fields: _FieldMergeView) -> StaticMergeMetadata:
    return StaticMergeMetadata(_fields=fields)


def _context(
    candidate, field_name, metadata, *, running_score: float = 0.0
) -> StrategyContext:
    return StrategyContext(
        candidate=candidate,
        field_name=field_name,
        merge_metadata=metadata,
        source_weights={DataSource.ATS: 0.7, DataSource.RESUME: 0.6},
        running_score=running_score,
    )


def test_source_weight_uses_max_weight_among_sources() -> None:
    candidate = make_candidate()
    metadata = _metadata(
        first_name=_FieldMergeView(
            conflict=False,
            contributing_sources=(DataSource.ATS,),
            sources_considered=(DataSource.ATS, DataSource.RESUME),
        )
    )
    result = SourceWeightStrategy().score(
        _context(candidate, "first_name", metadata)
    )
    assert result.delta == 0.7


def test_source_weight_no_sources_considered() -> None:
    candidate = make_candidate()
    metadata = _metadata()
    result = SourceWeightStrategy().score(
        _context(candidate, "first_name", metadata)
    )
    assert result.delta == 0.0


def test_agreement_bonus_applies_when_multiple_sources_agree() -> None:
    candidate = make_candidate()
    metadata = _metadata(
        first_name=_FieldMergeView(
            conflict=False,
            contributing_sources=(DataSource.ATS, DataSource.RESUME),
            sources_considered=(DataSource.ATS, DataSource.RESUME),
        )
    )
    result = AgreementStrategy(bonus=0.1).score(
        _context(candidate, "first_name", metadata)
    )
    assert result.delta == 0.1


def test_agreement_bonus_does_not_apply_on_conflict() -> None:
    candidate = make_candidate()
    metadata = _metadata(
        first_name=_FieldMergeView(
            conflict=True,
            contributing_sources=(DataSource.ATS, DataSource.RESUME),
            sources_considered=(DataSource.ATS, DataSource.RESUME),
        )
    )
    result = AgreementStrategy(bonus=0.1).score(
        _context(candidate, "first_name", metadata)
    )
    assert result.delta == 0.0


def test_conflict_penalty_applies_on_conflict() -> None:
    candidate = make_candidate()
    metadata = _metadata(
        first_name=_FieldMergeView(
            conflict=True,
            contributing_sources=(DataSource.ATS,),
            sources_considered=(DataSource.ATS, DataSource.RESUME),
        )
    )
    result = ConflictPenaltyStrategy(penalty=0.2).score(
        _context(candidate, "first_name", metadata)
    )
    assert result.delta == -0.2


def test_missing_field_zeroes_running_score_when_absent() -> None:
    candidate = make_candidate(skills=[])
    metadata = _metadata()
    result = MissingFieldStrategy().score(
        _context(candidate, "skills", metadata, running_score=0.6)
    )
    assert result.delta == -0.6


def test_missing_field_no_op_when_present() -> None:
    candidate = make_candidate(skills=["python"])
    metadata = _metadata()
    result = MissingFieldStrategy().score(
        _context(candidate, "skills", metadata, running_score=0.6)
    )
    assert result.delta == 0.0


def test_missing_field_handles_nested_dotted_field() -> None:
    candidate = make_candidate(contact=None)
    metadata = _metadata()
    result = MissingFieldStrategy().score(
        _context(candidate, "contact.email", metadata, running_score=0.5)
    )
    assert result.delta == -0.5
