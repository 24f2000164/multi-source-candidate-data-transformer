"""MergeEngine: takes ``list[Candidate]`` and produces one golden
``Candidate`` plus a ``MergeReport`` describing exactly how it was built.

Complexity is linear in the number of input candidates: every field is
resolved with a single pass over the source candidates (``O(F * N)`` for
``F`` fixed canonical fields and ``N`` sources), per the Sprint 5
requirement to keep merge complexity scalable.
"""

from typing import Any

from transformer.merge.exceptions import MergeError
from transformer.merge.field_resolver import FieldResolver
from transformer.merge.policy import MergePolicy, load_merge_policy
from transformer.merge.report import FieldMergeRecord, MergeReport
from transformer.merge.strategies import SourceValue
from transformer.models import Candidate, ContactInfo, DataSource, FieldProvenance

_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "first_name",
    "last_name",
    "external_id",
    "skills",
    "languages",
    "certifications",
    "experiences",
    "education",
)
_CONTACT_FIELDS: tuple[str, ...] = (
    "email",
    "phone",
    "location",
    "linkedin_url",
    "github_url",
)


class MergeEngine:
    """Orchestrates N-source merging into a single golden ``Candidate``."""

    def __init__(self, policy: MergePolicy | None = None) -> None:
        """Initialise the engine with a merge policy.

        Args:
            policy: The ``MergePolicy`` to apply. Defaults to the policy
                loaded from ``config/merge_policy.yaml``.
        """
        self._policy = policy if policy is not None else load_merge_policy()
        self._resolver = FieldResolver(self._policy)

    def merge(self, candidates: list[Candidate]) -> tuple[Candidate, MergeReport]:
        """Merge any number of source candidates into one golden candidate.

        Args:
            candidates: One or more ``Candidate`` instances, each typically
                produced by a single-source parser (ATS or resume), to be
                merged into a single golden record. A single-element list is
                a valid, supported call (single-source "merge").

        Returns:
            A tuple of ``(golden_candidate, merge_report)``.

        Raises:
            MergeError: If ``candidates`` is empty, or if a required field
                (``first_name``/``last_name``) cannot be resolved from any
                source.
        """
        if not candidates:
            raise MergeError("cannot merge an empty list of candidates")

        records: list[FieldMergeRecord] = []
        warnings: list[str] = []
        kwargs: dict[str, Any] = {}
        provenance: dict[str, FieldProvenance] = {}

        for field_name in _TOP_LEVEL_FIELDS:
            values = [
                SourceValue(
                    source=_candidate_source(candidate),
                    value=getattr(candidate, field_name),
                    confidence=_confidence_for(candidate, field_name),
                )
                for candidate in candidates
            ]
            result = self._resolver.resolve(field_name, values)
            self._apply_result(field_name, result, candidates, kwargs, provenance)
            records.append(self._record(result, candidates, field_name))
            warnings.extend(result.warnings)

        contact_kwargs: dict[str, Any] = {}
        for prov_key in _CONTACT_FIELDS:
            field_name = f"contact.{prov_key}"
            values = [
                SourceValue(
                    source=_candidate_source(candidate),
                    value=_contact_attr(candidate, prov_key),
                    confidence=_confidence_for(candidate, prov_key),
                )
                for candidate in candidates
            ]
            result = self._resolver.resolve(field_name, values)
            self._apply_result(prov_key, result, candidates, contact_kwargs, provenance)
            records.append(self._record(result, candidates, field_name))
            warnings.extend(result.warnings)

        if contact_kwargs:
            kwargs["contact"] = ContactInfo(**contact_kwargs)

        if not kwargs.get("first_name") or not kwargs.get("last_name"):
            raise MergeError(
                "could not resolve required fields 'first_name'/'last_name' "
                "from any source candidate"
            )

        kwargs["schema_version"] = candidates[0].schema_version
        kwargs["provenance"] = provenance

        golden = Candidate(**kwargs)
        report = MergeReport(fields=tuple(records), warnings=tuple(warnings))
        return golden, report

    @staticmethod
    def _apply_result(
        kwargs_key: str,
        result: Any,
        candidates: list[Candidate],
        kwargs: dict[str, Any],
        provenance: dict[str, FieldProvenance],
    ) -> None:
        if result.value is None or result.value == [] or result.value == "":
            return
        kwargs[kwargs_key] = result.value
        winner = result.winning_source or (
            result.contributing_sources[0] if result.contributing_sources else None
        )
        if winner is None:
            return
        for candidate in candidates:
            if _candidate_source(candidate) == winner:
                entry = candidate.provenance.get(kwargs_key)
                if entry is not None:
                    provenance[kwargs_key] = entry
                break

    @staticmethod
    def _record(
        result: Any, candidates: list[Candidate], field_name: str
    ) -> FieldMergeRecord:
        prov_key = field_name.removeprefix("contact.")
        source_provenance: dict[DataSource, FieldProvenance] = {}
        for candidate in candidates:
            entry = candidate.provenance.get(prov_key)
            if entry is not None:
                source_provenance[_candidate_source(candidate)] = entry
        return FieldMergeRecord(
            field=field_name,
            strategy=result.strategy,
            sources_considered=result.sources_considered,
            contributing_sources=result.contributing_sources,
            conflict=result.conflict,
            chosen_value_repr=repr(result.value),
            provenance=source_provenance,
        )


def _candidate_source(candidate: Candidate) -> DataSource:
    """Infer which source a single-source candidate originated from.

    Args:
        candidate: A single-source ``Candidate`` (the merge engine's input).

    Returns:
        The ``DataSource`` recorded against this candidate's fields.

    Raises:
        MergeError: If the candidate has no provenance at all, so its
            originating source cannot be determined.
    """
    if not candidate.provenance:
        raise MergeError(
            f"candidate {candidate.id} has no provenance; cannot determine "
            "its source for merging"
        )
    return next(iter(candidate.provenance.values())).source


def _contact_attr(candidate: Candidate, attr: str) -> Any:
    if candidate.contact is None:
        return None
    return getattr(candidate.contact, attr)


def _confidence_for(candidate: Candidate, field_name: str) -> float | None:
    if candidate.confidence is None:
        return None
    field_confidence = candidate.confidence.fields.get(field_name)
    return field_confidence.score if field_confidence is not None else None
