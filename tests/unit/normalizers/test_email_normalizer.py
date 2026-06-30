"""Unit tests for transformer.normalizers.email_normalizer."""

import pytest

from transformer.normalizers.email_normalizer import normalize_email


@pytest.mark.unit
class TestNormalizeEmail:
    def test_lowercases(self) -> None:
        assert normalize_email("John.Smith@Example.COM") == "john.smith@example.com"

    def test_trims_whitespace(self) -> None:
        assert normalize_email("  alice@example.com  ") == "alice@example.com"

    def test_idempotent(self) -> None:
        once = normalize_email("  Alice@Example.com  ")
        assert normalize_email(once) == once
