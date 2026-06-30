"""Confidence score models for field-level and record-level reliability."""

import math

from pydantic import BaseModel, ConfigDict, Field, field_validator

from transformer.models.enums import DataSource


class FieldConfidence(BaseModel):
    """Confidence score for a single field value.

    Attributes:
        score: Numeric confidence in the closed range ``[0.0, 1.0]``.
        source: The data source that produced this score.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score in the range [0.0, 1.0].",
    )
    source: DataSource = Field(
        ...,
        description="Data source that produced this confidence score.",
    )

    @field_validator("score")
    @classmethod
    def _finite_score(cls, v: float) -> float:
        """Reject NaN and infinite values.

        Args:
            v: Raw score value after ``ge``/``le`` constraint check.

        Returns:
            The validated finite score.

        Raises:
            ValueError: If ``score`` is NaN or infinite.
        """
        if not math.isfinite(v):
            raise ValueError("score must be a finite number")
        return v


class OverallConfidence(BaseModel):
    """Aggregate confidence score for a complete candidate record.

    Attributes:
        score: Overall confidence in the closed range ``[0.0, 1.0]``.
        fields: Per-field confidence scores keyed by canonical field name.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score in the range [0.0, 1.0].",
    )
    fields: dict[str, FieldConfidence] = Field(
        default_factory=dict,
        description="Per-field confidence scores keyed by field name.",
    )

    @field_validator("score")
    @classmethod
    def _finite_score(cls, v: float) -> float:
        """Reject NaN and infinite values.

        Args:
            v: Raw score value after ``ge``/``le`` constraint check.

        Returns:
            The validated finite score.

        Raises:
            ValueError: If ``score`` is NaN or infinite.
        """
        if not math.isfinite(v):
            raise ValueError("score must be a finite number")
        return v
