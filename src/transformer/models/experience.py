"""Work experience model for a candidate's employment history."""

from datetime import date
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from transformer.models._validators import deduplicate_strings, strip_non_empty


class WorkExperience(BaseModel):
    """A single work experience entry in a candidate's career history.

    Attributes:
        company: Name of the employer.
        title: Job title held during this period.
        start_date: Date when the position started.
        end_date: Date when the position ended; ``None`` indicates a current role.
        description: Free-text description of responsibilities and achievements.
        skills: Skills demonstrated or acquired in this role.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    company: str = Field(..., description="Employer name.")
    title: str = Field(..., description="Job title.")
    start_date: date = Field(..., description="Start date of the position.")
    end_date: date | None = Field(
        None, description="End date of the position; None means current role."
    )
    description: str | None = Field(None, description="Free-text role description.")
    skills: list[str] = Field(
        default_factory=list,
        max_length=500,
        description="Skills used or demonstrated in this role.",
    )

    @field_validator("company", "title", mode="before")
    @classmethod
    def _validate_required_str(cls, v: Any) -> Any:
        """Strip whitespace and reject blank required string fields.

        Args:
            v: Raw field value.

        Returns:
            Stripped non-blank string.

        Raises:
            ValueError: If the string is blank after stripping.
        """
        return strip_non_empty(v)

    @field_validator("description", mode="before")
    @classmethod
    def _validate_optional_str(cls, v: Any) -> Any:
        """Strip whitespace and reject blank optional string fields.

        Args:
            v: Raw field value.

        Returns:
            Stripped string or the original value if ``None``.

        Raises:
            ValueError: If a non-``None`` string is blank after stripping.
        """
        if v is None:
            return v
        return strip_non_empty(v)

    @field_validator("skills", mode="before")
    @classmethod
    def _dedup_skills(cls, v: Any) -> Any:
        """Remove duplicate and blank skill strings while preserving order.

        Args:
            v: Raw skills list.

        Returns:
            Deduplicated list of non-blank skill strings.
        """
        return deduplicate_strings(v)

    @field_validator("start_date")
    @classmethod
    def _no_future_start(cls, v: date) -> date:
        """Reject start dates that are in the future.

        Args:
            v: Parsed start date.

        Returns:
            Validated start date.

        Raises:
            ValueError: If ``start_date`` is after today.
        """
        if v > date.today():
            raise ValueError("start_date must not be in the future")
        return v

    @model_validator(mode="after")
    def _end_after_start(self) -> Self:
        """Ensure ``end_date`` is not earlier than ``start_date``.

        Returns:
            The validated model instance.

        Raises:
            ValueError: If ``end_date`` precedes ``start_date``.
        """
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self
