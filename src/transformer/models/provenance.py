"""Provenance model for tracking the origin of individual extracted fields."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from transformer.models.enums import DataSource


class FieldProvenance(BaseModel):
    """Records the origin and raw value of a single extracted field.

    Used by the merge engine and audit layer to trace where each value in the
    canonical model came from.

    Attributes:
        source: The system from which the field was extracted.
        raw_value: The raw, un-normalised string value as originally extracted.
        extracted_at: UTC timestamp of when the extraction occurred.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: DataSource = Field(
        ...,
        description="Origin system of the extracted value.",
    )
    raw_value: str = Field(
        ...,
        description="Raw, un-normalised value from the source document.",
    )
    extracted_at: datetime = Field(
        ...,
        description="UTC timestamp of when the value was extracted.",
    )
