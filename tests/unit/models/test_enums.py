"""Unit tests for transformer.models.enums."""

import pytest

from transformer.models.enums import DataSource


@pytest.mark.unit
class TestDataSource:
    """Tests for the DataSource enumeration."""

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_ats_value(self) -> None:
        assert DataSource.ATS == "ATS"

    def test_resume_value(self) -> None:
        assert DataSource.RESUME == "RESUME"

    def test_is_str_subclass(self) -> None:
        assert isinstance(DataSource.ATS, str)
        assert isinstance(DataSource.RESUME, str)

    def test_from_string_ats(self) -> None:
        assert DataSource("ATS") is DataSource.ATS

    def test_from_string_resume(self) -> None:
        assert DataSource("RESUME") is DataSource.RESUME

    def test_members_count(self) -> None:
        assert len(DataSource) == 2

    # ------------------------------------------------------------------
    # Negative path
    # ------------------------------------------------------------------

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            DataSource("LINKEDIN")

    def test_lowercase_raises(self) -> None:
        with pytest.raises(ValueError):
            DataSource("ats")
