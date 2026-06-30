"""Deterministic identity-key extraction for structured list merging.

Two entries from different sources are considered the "same" real-world
item if their identity key matches. Keys are normalized (trimmed,
lower-cased) so casing/whitespace differences between sources do not
prevent a match -- see IMPLEMENTATION_PLAN risk: "Merge of conflicting
nested lists needs a stable identity key".
"""

from datetime import date
import re
from typing import Any

IdentityKey = tuple[str, ...]

# Strips punctuation that can differ between sources for the same
# real-world entity (e.g. "NIT, Uttarakhand" vs "NIT Uttarakhand").
_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    # Lowercase → strip punctuation → collapse whitespace.
    # Punctuation removal handles comma variants like
    # "NIT, Uttarakhand" vs "NIT Uttarakhand" which are the same entity.
    text = str(value).strip().lower()
    text = _PUNCT_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


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
