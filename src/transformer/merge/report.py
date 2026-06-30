"""``MergeReport``: the audit trail produced alongside every golden Candidate.

The canonical ``Candidate`` model stores at most one ``FieldProvenance`` per
field (it is frozen and was not designed to fan out per source). The merge
engine must still "preserve provenance from ALL merged sources, never
overwrite provenance" -- it does so here, in the report, rather than by
mutating the frozen model.
"""

from pydantic import BaseModel, ConfigDict, Field

from transformer.models import DataSource, FieldProvenance


class FieldMergeRecord(BaseModel):
    """The full resolution detail for a single canonical field.

    Attributes:
        field: Canonical (dotted) field name, e.g. ``"contact.email"``.
        strategy: Name of the merge strategy applied.
        sources_considered: Every source that attempted to supply a value.
        contributing_sources: Sources whose non-empty value fed into the
            chosen value.
        conflict: ``True`` if sources disagreed and a choice was made.
        chosen_value_repr: Safe ``repr()`` of the resolved value (kept as a
            string so the report stays cheaply serialisable for arbitrarily
            nested values).
        provenance: Provenance entries from every source that had one for
            this field, keyed by source -- never overwritten, all sources
            preserved.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    field: str
    strategy: str
    sources_considered: tuple[DataSource, ...]
    contributing_sources: tuple[DataSource, ...]
    conflict: bool
    chosen_value_repr: str
    provenance: dict[DataSource, FieldProvenance] = Field(default_factory=dict)


class MergeReport(BaseModel):
    """Complete audit trail for one merge operation.

    Attributes:
        fields: Per-field resolution records, in resolution order.
        warnings: Human-readable, non-fatal warnings raised during merge
            (e.g. source disagreement notices).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    fields: tuple[FieldMergeRecord, ...]
    warnings: tuple[str, ...] = ()

    @property
    def merged_fields(self) -> tuple[str, ...]:
        """Names of every field that was resolved during the merge."""
        return tuple(record.field for record in self.fields)

    @property
    def conflicts(self) -> tuple[FieldMergeRecord, ...]:
        """Records for fields where sources disagreed."""
        return tuple(record for record in self.fields if record.conflict)

    @property
    def chosen_values(self) -> dict[str, str]:
        """Mapping of field name -> safe repr of the value that was chosen."""
        return {record.field: record.chosen_value_repr for record in self.fields}

    @property
    def merge_strategy(self) -> dict[str, str]:
        """Mapping of field name -> strategy name used to resolve it."""
        return {record.field: record.strategy for record in self.fields}
