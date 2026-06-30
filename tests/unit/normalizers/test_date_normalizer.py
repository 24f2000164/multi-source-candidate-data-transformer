"""Unit tests for transformer.normalizers.date_normalizer."""

from datetime import date

import pytest

from transformer.normalizers.date_normalizer import coerce_date
from transformer.normalizers.exceptions import NormalizationError


@pytest.mark.unit
class TestCoerceDate:
    def test_date_instance_passed_through_unchanged(self) -> None:
        d = date(2020, 1, 1)
        assert coerce_date(d) is d

    def test_iso_string_parses(self) -> None:
        assert coerce_date("2020-01-15") == date(2020, 1, 15)

    def test_alternate_format_parses(self) -> None:
        assert coerce_date("January 15, 2020") == date(2020, 1, 15)

    def test_unparseable_string_raises(self) -> None:
        with pytest.raises(NormalizationError):
            coerce_date("not a date")

    def test_idempotent(self) -> None:
        once = coerce_date("2020-01-15")
        assert coerce_date(once) == once
