"""Unit tests for transformer.normalizers.string_normalizer."""

import pytest

from transformer.normalizers.string_normalizer import (
    clean,
    collapse_whitespace,
    normalize_unicode,
    title_case_name,
    trim,
)


@pytest.mark.unit
class TestTrim:
    def test_strips_leading_and_trailing_whitespace(self) -> None:
        assert trim("  hello  ") == "hello"

    def test_no_op_on_already_trimmed(self) -> None:
        assert trim("hello") == "hello"


@pytest.mark.unit
class TestCollapseWhitespace:
    def test_collapses_internal_runs(self) -> None:
        assert collapse_whitespace("a   b\t\tc\nd") == "a b c d"

    def test_preserves_single_spaces(self) -> None:
        assert collapse_whitespace("a b c") == "a b c"


@pytest.mark.unit
class TestNormalizeUnicode:
    def test_nfkc_normalizes_compatibility_characters(self) -> None:
        # U+FB01 LATIN SMALL LIGATURE FI -> "fi"
        assert normalize_unicode("\ufb01le") == "file"


@pytest.mark.unit
class TestTitleCaseName:
    def test_lowercase_name_is_capitalized(self) -> None:
        assert title_case_name("john") == "John"

    def test_uppercase_name_is_capitalized(self) -> None:
        assert title_case_name("JOHN") == "John"

    def test_mixed_case_segment_left_untouched(self) -> None:
        assert title_case_name("McDonald") == "McDonald"

    def test_hyphenated_name(self) -> None:
        assert title_case_name("mary-jane") == "Mary-Jane"

    def test_multi_word_name(self) -> None:
        assert title_case_name("john smith") == "John Smith"


@pytest.mark.unit
class TestClean:
    def test_full_pipeline(self) -> None:
        assert clean("  hello   world  ") == "hello world"

    def test_idempotent(self) -> None:
        once = clean("  hello   world  ")
        assert clean(once) == once
