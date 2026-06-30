"""Unit tests for transformer.normalizers.phone_normalizer."""

import pytest

from transformer.normalizers.phone_normalizer import normalize_phone


@pytest.mark.unit
class TestNormalizePhone:
    def test_us_number_without_formatting(self) -> None:
        assert normalize_phone("4155552671", default_region="US") == "+14155552671"

    def test_us_number_with_formatting(self) -> None:
        assert normalize_phone("(415) 555-2671", default_region="US") == "+14155552671"

    def test_already_e164_with_plus_prefix(self) -> None:
        assert normalize_phone("+14155552671") == "+14155552671"

    def test_explicit_country_code_overrides_default_region(self) -> None:
        # UK number, default region left as US; the leading "+" means the
        # explicit country code wins regardless of default_region.
        assert normalize_phone("+442079460958", default_region="US") == "+442079460958"

    def test_different_default_region(self) -> None:
        assert normalize_phone("020 7946 0958", default_region="GB") == "+442079460958"

    def test_unparseable_input_returns_trimmed_original(self) -> None:
        assert normalize_phone("  not-a-phone  ") == "not-a-phone"

    def test_empty_string_returns_empty(self) -> None:
        assert normalize_phone("   ") == ""

    def test_idempotent(self) -> None:
        once = normalize_phone("4155552671", default_region="US")
        assert normalize_phone(once, default_region="US") == once
