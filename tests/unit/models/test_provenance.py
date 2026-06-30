"""Unit tests for transformer.models.provenance."""

from datetime import UTC, datetime

from pydantic import ValidationError
import pytest

from transformer.models.enums import DataSource
from transformer.models.provenance import FieldProvenance


def _make_provenance(**overrides: object) -> FieldProvenance:
    defaults: dict[str, object] = {
        "source": DataSource.ATS,
        "raw_value": "John",
        "extracted_at": datetime(2024, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return FieldProvenance(**defaults)  # type: ignore[arg-type]


@pytest.mark.unit
class TestFieldProvenance:
    """Tests for FieldProvenance."""

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_valid_creation(self) -> None:
        prov = _make_provenance()
        assert prov.source == DataSource.ATS
        assert prov.raw_value == "John"

    def test_resume_source(self) -> None:
        prov = _make_provenance(source=DataSource.RESUME)
        assert prov.source == DataSource.RESUME

    def test_raw_value_preserved(self) -> None:
        prov = _make_provenance(raw_value="  raw  string  ")
        assert prov.raw_value == "  raw  string  "

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_frozen(self) -> None:
        prov = _make_provenance()
        with pytest.raises(ValidationError):
            prov.raw_value = "changed"  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Negative path
    # ------------------------------------------------------------------

    def test_missing_source_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldProvenance(
                raw_value="x",
                extracted_at=datetime(2024, 1, 1, tzinfo=UTC),
            )

    def test_missing_raw_value_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldProvenance(
                source=DataSource.ATS,
                extracted_at=datetime(2024, 1, 1, tzinfo=UTC),
            )

    def test_missing_extracted_at_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldProvenance(source=DataSource.ATS, raw_value="x")

    def test_invalid_source_raises(self) -> None:
        with pytest.raises(ValidationError):
            FieldProvenance(
                source="INVALID",
                raw_value="x",
                extracted_at=datetime(2024, 1, 1, tzinfo=UTC),
            )

    # ------------------------------------------------------------------
    # Extra fields forbidden
    # ------------------------------------------------------------------

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FieldProvenance(
                source=DataSource.ATS,
                raw_value="x",
                extracted_at=datetime(2024, 1, 1, tzinfo=UTC),
                unexpected="field",
            )
