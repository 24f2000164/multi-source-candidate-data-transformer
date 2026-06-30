"""Pure string normalization helpers.

These functions are intentionally side-effect free and operate on plain
``str`` values so they can be reused by every other normalizer in this
package without coupling to the Candidate model.
"""

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")


def trim(value: str) -> str:
    """Strip leading and trailing whitespace.

    Args:
        value: Raw string.

    Returns:
        The string with leading/trailing whitespace removed.
    """
    return value.strip()


def collapse_whitespace(value: str) -> str:
    """Collapse runs of internal whitespace into a single space.

    Args:
        value: Raw string.

    Returns:
        String with internal whitespace runs collapsed to one space.
    """
    return _WHITESPACE_RE.sub(" ", value)


def normalize_unicode(value: str) -> str:
    """Apply NFKC Unicode normalization.

    Args:
        value: Raw string.

    Returns:
        The NFKC-normalised string.
    """
    return unicodedata.normalize("NFKC", value)


def title_case_name(value: str) -> str:
    """Apply name-appropriate title casing.

    Preserves internal capitalisation patterns common in names (e.g.
    ``"McDonald"``, ``"O'Brien"``) by only adjusting the first letter of each
    whitespace/hyphen-delimited segment when the segment is fully upper or
    fully lower case; mixed-case segments are left untouched.

    Args:
        value: Raw name string.

    Returns:
        The name with simple title casing applied.
    """

    def _cap_segment(segment: str) -> str:
        if segment.isupper() or segment.islower():
            return segment[:1].upper() + segment[1:].lower() if segment else segment
        return segment

    parts = re.split(r"([\s\-]+)", value)
    return "".join(
        part if re.fullmatch(r"[\s\-]+", part) else _cap_segment(part) for part in parts
    )


def clean(value: str) -> str:
    """Apply the standard normalization pipeline: trim + collapse + unicode.

    Args:
        value: Raw string.

    Returns:
        The fully cleaned string.
    """
    return collapse_whitespace(trim(normalize_unicode(value)))
