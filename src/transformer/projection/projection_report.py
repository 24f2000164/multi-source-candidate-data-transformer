"""The ``ProjectionReport`` produced by every projection-engine run."""

from pydantic import BaseModel, ConfigDict, Field


class ProjectionReport(BaseModel):
    """Metadata describing one projection-engine run.

    Deliberately does NOT contain the projected output itself -- the output
    dict can be large and is returned separately by ``ProjectionEngine``.
    This keeps the report cheap to log/store independently of payload size.

    Attributes:
        projection_type: Name of the projection type that was run.
        field_count: Number of top-level keys in the projected output.
        warnings: Any non-fatal issues noticed during projection.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    projection_type: str
    field_count: int = Field(..., ge=0)
    warnings: tuple[str, ...] = ()
