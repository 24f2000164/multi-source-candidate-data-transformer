"""Unit tests for transformer.parsers.resume.extractors."""

from transformer.parsers.resume import extractors


class TestExtractEmail:
    def test_finds_email(self) -> None:
        assert (
            extractors.extract_email("Contact: john@example.com") == "john@example.com"
        )

    def test_no_email_returns_none(self) -> None:
        assert extractors.extract_email("no contact info here") is None

    def test_finds_all_emails_deduplicated(self) -> None:
        text = "a@x.com b@y.com a@x.com"
        assert extractors.extract_all_emails(text) == ["a@x.com", "b@y.com"]


class TestExtractPhone:
    def test_finds_phone(self) -> None:
        assert extractors.extract_phone("Call +1 555-123-4567 now") is not None

    def test_short_digit_sequence_ignored(self) -> None:
        assert extractors.extract_phone("Room 12") is None

    def test_no_phone_returns_none(self) -> None:
        assert extractors.extract_phone("no number here") is None


class TestExtractLinkedin:
    def test_finds_url_and_normalises_scheme(self) -> None:
        result = extractors.extract_linkedin_url("linkedin.com/in/janedoe")
        assert result == "https://linkedin.com/in/janedoe"

    def test_preserves_existing_scheme(self) -> None:
        result = extractors.extract_linkedin_url("https://www.linkedin.com/in/janedoe")
        assert result is not None and result.startswith("https://")

    def test_no_match_returns_none(self) -> None:
        assert extractors.extract_linkedin_url("no profile here") is None


class TestExtractGithub:
    def test_finds_url(self) -> None:
        assert extractors.extract_github_url("github.com/janedoe") == (
            "https://github.com/janedoe"
        )

    def test_no_match_returns_none(self) -> None:
        assert extractors.extract_github_url("no profile here") is None


class TestExtractListItems:
    def test_splits_on_commas(self) -> None:
        assert extractors.extract_list_items("Python, Java, SQL") == [
            "Python",
            "Java",
            "SQL",
        ]

    def test_splits_on_bullets_and_newlines(self) -> None:
        text = "\u2022 Python\n\u2022 Java"
        assert extractors.extract_list_items(text) == ["Python", "Java"]

    def test_dedupes_case_insensitively(self) -> None:
        assert extractors.extract_list_items("Python, python, Java") == [
            "Python",
            "Java",
        ]

    def test_empty_text_returns_empty_list(self) -> None:
        assert extractors.extract_list_items("") == []


class TestExtractDates:
    def test_finds_month_year_range(self) -> None:
        result = extractors.extract_dates("Jan 2020 - Dec 2022 Engineer")
        assert result == [("Jan 2020", "Dec 2022")]

    def test_finds_present_as_end(self) -> None:
        result = extractors.extract_dates("2021 - Present")
        assert result == [("2021", "Present")]

    def test_no_dates_returns_empty(self) -> None:
        assert extractors.extract_dates("no dates in this line") == []
