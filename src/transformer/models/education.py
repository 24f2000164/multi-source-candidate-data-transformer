"""Education and certification models for a candidate's academic history."""

from datetime import date
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from transformer.models._validators import strip_non_empty

_MIN_GPA: float = 0.0
_MAX_GPA: float = 4.0


class Education(BaseModel):
    """A single academic credential or degree entry.

    Attributes:
        institution: Name of the awarding institution.
        degree: Degree title (e.g., ``"Bachelor of Science"``).
        field_of_study: Major or area of study.
        start_date: Date when studies started.
        end_date: Date when studies ended; ``None`` if still in progress.
        gpa: Grade Point Average on a 0.0-4.0 scale.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    institution: str = Field(..., description="Name of the awarding institution.")
    degree: str = Field(..., description="Degree title.")
    field_of_study: str | None = Field(None, description="Major or area of study.")
    start_date: date | None = Field(None, description="Study start date.")
    end_date: date | None = Field(None, description="Study end date; None if ongoing.")
    gpa: float | None = Field(
        None,
        ge=_MIN_GPA,
        le=_MAX_GPA,
        description=f"GPA on a {_MIN_GPA}-{_MAX_GPA} scale.",
    )

    @field_validator("institution", "degree", mode="before")
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

    @field_validator("field_of_study", mode="before")
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

    @model_validator(mode="after")
    def _end_after_start(self) -> Self:
        """Ensure ``end_date`` is not earlier than ``start_date`` when both are set.

        Returns:
            The validated model instance.

        Raises:
            ValueError: If ``end_date`` precedes ``start_date``.
        """
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must not be before start_date")
        return self


class Certification(BaseModel):
    """A professional certification or licence held by the candidate.

    Attributes:
        name: Official name of the certification.
        issuer: Organisation that issued the certification.
        issued_date: Date the certification was awarded.
        expiry_date: Expiry date; ``None`` if it does not expire.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., description="Official certification name.")
    issuer: str | None = Field(None, description="Issuing organisation.")
    issued_date: date | None = Field(
        None, description="Date the certification was awarded."
    )
    expiry_date: date | None = Field(
        None, description="Expiry date; None if perpetual."
    )

    @field_validator("name", mode="before")
    @classmethod
    def _validate_name(cls, v: Any) -> Any:
        """Strip whitespace and reject blank certification names.

        Args:
            v: Raw name value.

        Returns:
            Stripped non-blank name string.

        Raises:
            ValueError: If the name is blank after stripping.
        """
        return strip_non_empty(v)

    @field_validator("issuer", mode="before")
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

    @model_validator(mode="after")
    def _expiry_after_issued(self) -> Self:
        """Ensure ``expiry_date`` is not earlier than ``issued_date``.

        Returns:
            The validated model instance.

        Raises:
            ValueError: If ``expiry_date`` precedes ``issued_date``.
        """
        if (
            self.issued_date is not None
            and self.expiry_date is not None
            and self.expiry_date < self.issued_date
        ):
            raise ValueError("expiry_date must not be before issued_date")
        return self
