"""Unit tests for transformer.merge.strategies."""

import pytest

from transformer.merge.strategies import (
    FirstNonEmptyStrategy,
    HighestConfidenceStrategy,
    SourcePriorityStrategy,
    SourceValue,
    UnionStrategy,
)
from transformer.models import DataSource

_PRIORITY = (DataSource.ATS, DataSource.RESUME)


@pytest.mark.unit
class TestSourcePriorityStrategy:
    def test_picks_higher_priority_source(self) -> None:
        strategy = SourcePriorityStrategy()
        values = [
            SourceValue(DataSource.RESUME, "Resume Value"),
            SourceValue(DataSource.ATS, "ATS Value"),
        ]
        result = strategy.apply(values, _PRIORITY)
        assert result.value == "ATS Value"
        assert result.winning_source == DataSource.ATS

    def test_falls_back_when_higher_priority_is_empty(self) -> None:
        strategy = SourcePriorityStrategy()
        values = [
            SourceValue(DataSource.ATS, None),
            SourceValue(DataSource.RESUME, "X"),
        ]
        result = strategy.apply(values, _PRIORITY)
        assert result.value == "X"
        assert result.winning_source == DataSource.RESUME

    def test_flags_conflict_on_disagreement(self) -> None:
        strategy = SourcePriorityStrategy()
        values = [SourceValue(DataSource.ATS, "A"), SourceValue(DataSource.RESUME, "B")]
        result = strategy.apply(values, _PRIORITY)
        assert result.conflict is True

    def test_no_conflict_when_values_match(self) -> None:
        strategy = SourcePriorityStrategy()
        values = [SourceValue(DataSource.ATS, "A"), SourceValue(DataSource.RESUME, "A")]
        result = strategy.apply(values, _PRIORITY)
        assert result.conflict is False

    def test_all_empty_returns_none(self) -> None:
        strategy = SourcePriorityStrategy()
        values = [SourceValue(DataSource.ATS, None), SourceValue(DataSource.RESUME, "")]
        result = strategy.apply(values, _PRIORITY)
        assert result.value is None
        assert result.winning_source is None


@pytest.mark.unit
class TestFirstNonEmptyStrategy:
    def test_picks_first_non_empty_in_priority_order(self) -> None:
        strategy = FirstNonEmptyStrategy()
        values = [SourceValue(DataSource.RESUME, "R"), SourceValue(DataSource.ATS, "A")]
        result = strategy.apply(values, _PRIORITY)
        assert result.value == "A"

    def test_never_flags_conflict(self) -> None:
        strategy = FirstNonEmptyStrategy()
        values = [SourceValue(DataSource.ATS, "A"), SourceValue(DataSource.RESUME, "B")]
        result = strategy.apply(values, _PRIORITY)
        assert result.conflict is False


@pytest.mark.unit
class TestHighestConfidenceStrategy:
    def test_picks_highest_confidence_value(self) -> None:
        strategy = HighestConfidenceStrategy()
        values = [
            SourceValue(DataSource.ATS, "A", confidence=0.5),
            SourceValue(DataSource.RESUME, "B", confidence=0.9),
        ]
        result = strategy.apply(values, _PRIORITY)
        assert result.value == "B"
        assert result.winning_source == DataSource.RESUME

    def test_falls_back_to_source_priority_without_confidence(self) -> None:
        strategy = HighestConfidenceStrategy()
        values = [SourceValue(DataSource.RESUME, "R"), SourceValue(DataSource.ATS, "A")]
        result = strategy.apply(values, _PRIORITY)
        assert result.value == "A"


@pytest.mark.unit
class TestUnionStrategy:
    def test_uses_supplied_merge_function(self) -> None:
        def merge_fn(ordered: list[SourceValue]) -> list[str]:
            merged: list[str] = []
            for sv in ordered:
                merged.extend(sv.value)
            return merged

        strategy = UnionStrategy(merge_fn)
        values = [
            SourceValue(DataSource.ATS, ["a", "b"]),
            SourceValue(DataSource.RESUME, ["c"]),
        ]
        result = strategy.apply(values, _PRIORITY)
        assert result.value == ["a", "b", "c"]
        assert set(result.contributing_sources) == {DataSource.ATS, DataSource.RESUME}

    def test_all_empty_returns_empty_list(self) -> None:
        strategy = UnionStrategy(lambda ordered: [])
        values = [SourceValue(DataSource.ATS, []), SourceValue(DataSource.RESUME, [])]
        result = strategy.apply(values, _PRIORITY)
        assert result.value == []
