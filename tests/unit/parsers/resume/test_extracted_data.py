"""Unit tests for transformer.parsers.resume.extracted_data."""

import pytest

from transformer.parsers.resume.extracted_data import (
    ExtractedResumeData,
    RawExperienceEntry,
)


class TestExtractedResumeData:
    def test_constructs_with_defaults(self) -> None:
        data = ExtractedResumeData()
        assert data.first_name is None
        assert data.skills == []
        assert data.experience_entries == []

    def test_accepts_partial_data(self) -> None:
        data = ExtractedResumeData(first_name="Jane", skills=["Python"])
        assert data.first_name == "Jane"
        assert data.skills == ["Python"]

    def test_rejects_unknown_fields(self) -> None:
        with pytest.raises(Exception):  # noqa: B017 - pydantic ValidationError
            ExtractedResumeData(unknown_field="x")  # type: ignore[call-arg]

    def test_no_file_or_regex_dependency(self) -> None:
        # ExtractedResumeData is independently constructible -- it knows
        # nothing about files, PDFs, or regex extraction.
        entry = RawExperienceEntry(company="Acme", title="Engineer")
        data = ExtractedResumeData(
            first_name="Jane", last_name="Doe", experience_entries=[entry]
        )
        assert data.experience_entries[0].company == "Acme"
