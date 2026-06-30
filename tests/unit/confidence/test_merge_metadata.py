"""Unit tests for transformer.confidence.merge_metadata."""

from dataclasses import dataclass

from transformer.confidence.merge_metadata import from_merge_report, from_single_source
from transformer.models import DataSource


@dataclass
class _FakeRecord:
    field: str
    conflict: bool
    contributing_sources: tuple[DataSource, ...]
    sources_considered: tuple[DataSource, ...]


@dataclass
class _FakeReport:
    fields: tuple[_FakeRecord, ...]


def test_from_merge_report_reflects_conflict_and_counts() -> None:
    report = _FakeReport(
        fields=(
            _FakeRecord(
                field="contact.email",
                conflict=True,
                contributing_sources=(DataSource.ATS, DataSource.RESUME),
                sources_considered=(DataSource.ATS, DataSource.RESUME),
            ),
        )
    )
    metadata = from_merge_report(report)
    assert metadata.field_conflict("contact.email") is True
    assert metadata.contributing_source_count("contact.email") == 2
    assert metadata.sources_considered("contact.email") == (
        DataSource.ATS,
        DataSource.RESUME,
    )


def test_unknown_field_does_not_raise() -> None:
    report = _FakeReport(fields=())
    metadata = from_merge_report(report)
    assert metadata.field_conflict("nonexistent") is False
    assert metadata.contributing_source_count("nonexistent") == 0
    assert metadata.sources_considered("nonexistent") == ()


def test_from_single_source_never_conflicts() -> None:
    metadata = from_single_source(DataSource.RESUME)
    assert metadata.field_conflict("first_name") is False
    assert metadata.contributing_source_count("first_name") == 1
    assert metadata.sources_considered("first_name") == (DataSource.RESUME,)
