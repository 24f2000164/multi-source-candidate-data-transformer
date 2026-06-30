"""``MergeMetadata``: the only view the confidence package has of merge results.

This module is the sole seam between ``transformer.merge`` and
``transformer.confidence``. Strategies and the aggregator depend only on the
``MergeMetadata`` protocol below -- never on ``MergeReport`` -- so a future
change to the merge package's internal record format cannot ripple into
confidence scoring as long as this adapter still produces a valid
``MergeMetadata``.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from transformer.models import DataSource


@runtime_checkable
class MergeMetadata(Protocol):
    """Minimal, read-only view of merge outcomes needed for confidence scoring.

    Implementations must be immutable and must never raise for an unknown
    field name -- an unrecognised field is treated as "no data" (see
    ``_UnknownFieldMetadata`` / edge case handling below), not an error.
    """

    def field_conflict(self, field: str) -> bool:
        """Whether sources disagreed on the value for ``field``.

        Args:
            field: Canonical (dotted) field name, e.g. ``"contact.email"``.

        Returns:
            ``True`` if multiple sources contributed conflicting values.
        """
        ...

    def contributing_source_count(self, field: str) -> int:
        """Number of sources whose non-empty value fed into ``field``.

        Args:
            field: Canonical (dotted) field name.

        Returns:
            Count of contributing sources (``0`` if none/unknown).
        """
        ...

    def sources_considered(self, field: str) -> tuple[DataSource, ...]:
        """Every source that attempted to supply a value for ``field``.

        Args:
            field: Canonical (dotted) field name.

        Returns:
            Tuple of sources considered (empty if none/unknown).
        """
        ...


@dataclass(frozen=True)
class _FieldMergeView:
    """Internal per-field snapshot used by the concrete ``MergeMetadata`` impls."""

    conflict: bool
    contributing_sources: tuple[DataSource, ...]
    sources_considered: tuple[DataSource, ...]


@dataclass(frozen=True)
class StaticMergeMetadata:
    """A concrete, immutable ``MergeMetadata`` backed by a plain mapping.

    Unknown field keys resolve to "no conflict, no contributors" rather than
    raising, satisfying the edge-case requirement that invalid/partial
    metadata must not raise.
    """

    _fields: dict[str, _FieldMergeView]

    def field_conflict(self, field: str) -> bool:
        """See ``MergeMetadata.field_conflict``."""
        view = self._fields.get(field)
        return view.conflict if view is not None else False

    def contributing_source_count(self, field: str) -> int:
        """See ``MergeMetadata.contributing_source_count``."""
        view = self._fields.get(field)
        return len(view.contributing_sources) if view is not None else 0

    def sources_considered(self, field: str) -> tuple[DataSource, ...]:
        """See ``MergeMetadata.sources_considered``."""
        view = self._fields.get(field)
        return view.sources_considered if view is not None else ()


def from_merge_report(report: object) -> MergeMetadata:
    """Build ``MergeMetadata`` from a ``transformer.merge.MergeReport``.

    Imports ``MergeReport``'s attributes structurally (duck-typed access via
    ``report.fields``) rather than importing the ``transformer.merge``
    package, so the confidence package has zero static import of
    ``transformer.merge`` internals.

    Args:
        report: A ``MergeReport``-like object exposing a ``fields`` iterable
            of records with ``field``, ``conflict``, ``contributing_sources``,
            and ``sources_considered`` attributes.

    Returns:
        An immutable ``MergeMetadata`` view over the report.
    """
    fields: dict[str, _FieldMergeView] = {}
    for record in getattr(report, "fields", ()):
        fields[record.field] = _FieldMergeView(
            conflict=bool(record.conflict),
            contributing_sources=tuple(record.contributing_sources),
            sources_considered=tuple(record.sources_considered),
        )
    return StaticMergeMetadata(_fields=fields)


def from_single_source(source: DataSource) -> MergeMetadata:
    """Build ``MergeMetadata`` for a candidate that never went through a merge.

    Every field is treated as having no conflict and exactly one
    contributor: ``source``. Used when a candidate was built from a single
    ATS or resume record with no ``MergeReport`` available.

    Args:
        source: The single ``DataSource`` that produced the candidate.

    Returns:
        A ``MergeMetadata`` whose queries always report a single,
        non-conflicting contributor for any field name.
    """
    return _SingleSourceMergeMetadata(source=source)


@dataclass(frozen=True)
class _SingleSourceMergeMetadata:
    """``MergeMetadata`` for a single-source candidate (no real merge occurred)."""

    source: DataSource

    def field_conflict(self, field: str) -> bool:
        """Always ``False``: a single source cannot conflict with itself."""
        return False

    def contributing_source_count(self, field: str) -> int:
        """Always ``1``: the sole source is treated as contributing every field."""
        return 1

    def sources_considered(self, field: str) -> tuple[DataSource, ...]:
        """Always the single source."""
        return (self.source,)
