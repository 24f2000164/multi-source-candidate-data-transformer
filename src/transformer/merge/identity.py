"""Deterministic identity-key extraction for structured list merging.

Two entries from different sources are considered the "same" real-world
item if their identity key matches. Keys are normalized (trimmed,
lower-cased) so casing/whitespace differences between sources do not
prevent a match -- see IMPLEMENTATION_PLAN risk: "Merge of conflicting
nested lists needs a stable identity key".
"""

from datetime import date
from typing import Any

IdentityKey = tuple[str, ...]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip().lower()


def identity_key(item: Any, fields: tuple[str, ...]) -> IdentityKey:
    """Build a normalized identity key from named attributes of ``item``.

    Args:
        item: A model instance (``WorkExperience``, ``Education``, or
            ``Certification``) or any object exposing the named attributes.
        fields: Attribute names that jointly identify the entry, as
            configured in the merge policy's ``identity_keys`` (e.g.
            ``("company", "title", "start_date")`` for experience).

    Returns:
        A tuple of normalized (trimmed, lower-cased) string values, one per
        field, suitable for use as a dict key during identity matching.
    """
    return tuple(_norm(getattr(item, name, None)) for name in fields)
