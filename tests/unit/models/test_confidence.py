"""Unit tests for transformer.models.confidence."""

import math

from pydantic import ValidationError
import pytest

from transformer.models.confidence import FieldConfidence, OverallConfidence
from transformer.models.enums import DataSource


@pytest.mark.unit
class TestFieldConfidence:
    """Tests for FieldConfidence."""

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_minimum_score(self) -> None:
        fc = FieldConfidence(score=0.0, source=DataSource.ATS)
        assert fc.score == 0.0

    def test_maximum_score(self) -> None:
        fc = FieldConfidence(score=1.0, source=DataSource.ATS)
        assert fc.score == 1.0

    def test_mid_score(self) -> None:
        fc = FieldConfidence(score=0.75, source=DataSource.RESUME)
        assert fc.score == 0.75

    def test_source_preserved(self) -> None:
        fc = FieldConfidence(score=0.5, source=DataSource.RESUME)
        assert fc.source == DataSource.RESUME

    # ------------------------------------------------------------------
    # Negative path
    # ------------------------------------------------------------------

    def test_score_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldConfidence(score=-0.1, source=DataSource.ATS)

    def test_score_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldConfidence(score=1.1, source=DataSource.ATS)

    def test_missing_source_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldConfidence(score=0.5)

    def test_missing_score_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldConfidence(source=DataSource.ATS)

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_nan_score_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldConfidence(score=math.nan, source=DataSource.ATS)

    def test_positive_infinity_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldConfidence(score=math.inf, source=DataSource.ATS)

    def test_negative_infinity_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldConfidence(score=-math.inf, source=DataSource.ATS)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FieldConfidence(score=0.5, source=DataSource.ATS, unexpected="x")

    def test_frozen(self) -> None:
        fc = FieldConfidence(score=0.5, source=DataSource.ATS)
        with pytest.raises(ValidationError):
            fc.score = 0.9  # type: ignore[misc]


@pytest.mark.unit
class TestOverallConfidence:
    """Tests for OverallConfidence."""

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_valid_with_empty_fields(self) -> None:
        oc = OverallConfidence(score=0.8)
        assert oc.score == 0.8
        assert oc.fields == {}

    def test_valid_with_field_scores(self) -> None:
        oc = OverallConfidence(
            score=0.9,
            fields={
                "first_name": FieldConfidence(score=1.0, source=DataSource.ATS),
                "email": FieldConfidence(score=0.8, source=DataSource.RESUME),
            },
        )
        assert oc.fields["first_name"].score == 1.0

    def test_boundary_scores(self) -> None:
        assert OverallConfidence(score=0.0).score == 0.0
        assert OverallConfidence(score=1.0).score == 1.0

    # ------------------------------------------------------------------
    # Negative path
    # ------------------------------------------------------------------

    def test_score_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            OverallConfidence(score=-0.01)

    def test_score_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            OverallConfidence(score=1.01)

    def test_missing_score_raises(self) -> None:
        with pytest.raises(ValidationError):
            OverallConfidence()  # type: ignore[call-arg]

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_nan_score_raises(self) -> None:
        with pytest.raises(ValidationError):
            OverallConfidence(score=math.nan)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            OverallConfidence(score=0.5, unexpected="x")

    def test_frozen(self) -> None:
        oc = OverallConfidence(score=0.5)
        with pytest.raises(ValidationError):
            oc.score = 0.9  # type: ignore[misc]
