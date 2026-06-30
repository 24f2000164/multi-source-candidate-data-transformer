"""Pure, stateless field-extraction functions for resume text.

Each function takes a plain-text chunk and returns matched value(s).  No
shared state, no knowledge of sections/blocks/Candidate -- regex patterns are
compiled once at import time as module-level constants.  Named after
responsibility (``extract_email``), not implementation, so the regex
internals can change without callers caring.
"""

import re

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.\-]?)?(?:\(\d{2,4}\)[\s.\-]?)?\d{3,5}[\s.\-]?\d{3,4}[\s.\-]?\d{0,4}"
)
_LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_%/]+", re.IGNORECASE
)
_GITHUB_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_]+", re.IGNORECASE
)
_MIN_PHONE_DIGITS = 7
_LIST_SPLIT_RE = re.compile(r"[,•\u2022|\n;]+")


def extract_email(text: str) -> str | None:
    """Find the first email address in ``text``.

    Args:
        text: Plain text to search.

    Returns:
        The first matched email address, or ``None`` if no match.
    """
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_all_emails(text: str) -> list[str]:
    """Find every distinct email address in ``text``, preserving order.

    Args:
        text: Plain text to search.

    Returns:
        Deduplicated list of matched email addresses.
    """
    seen: list[str] = []
    for match in _EMAIL_RE.findall(text):
        if match not in seen:
            seen.append(match)
    return seen


def extract_phone(text: str) -> str | None:
    """Find the first plausible phone number in ``text``.

    Args:
        text: Plain text to search.

    Returns:
        The first matched phone number with at least
        ``_MIN_PHONE_DIGITS`` digits, or ``None`` if no match.
    """
    for match in _PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if len(digits) >= _MIN_PHONE_DIGITS:
            return match.group(0).strip()
    return None


def extract_linkedin_url(text: str) -> str | None:
    """Find the first LinkedIn profile URL in ``text``.

    Args:
        text: Plain text to search.

    Returns:
        The matched URL (normalised with an ``https://`` scheme), or
        ``None`` if no match.
    """
    match = _LINKEDIN_RE.search(text)
    if not match:
        return None
    return _ensure_scheme(match.group(0))


def extract_github_url(text: str) -> str | None:
    """Find the first GitHub profile URL in ``text``.

    Args:
        text: Plain text to search.

    Returns:
        The matched URL (normalised with an ``https://`` scheme), or
        ``None`` if no match.
    """
    match = _GITHUB_RE.search(text)
    if not match:
        return None
    return _ensure_scheme(match.group(0))


def extract_list_items(section_text: str) -> list[str]:
    """Split a section body into discrete items (skills, languages, etc.).

    Splits on commas, bullets, pipes, semicolons, and newlines; strips
    whitespace and drops empty entries while preserving order and removing
    duplicates (case-insensitive).

    Args:
        section_text: Raw text body of a section (e.g. the Skills section).

    Returns:
        Ordered, deduplicated list of trimmed item strings.
    """
    seen: set[str] = set()
    result: list[str] = []
    for raw_item in _LIST_SPLIT_RE.split(section_text):
        item = raw_item.strip(" \t-\u2022")
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


_DATE_RANGE_RE = re.compile(
    r"(?P<start>(?:[A-Za-z]{3,9}\.?\s+\d{4})|(?:\d{1,2}/\d{4})|(?:\d{4}))"
    r"\s*(?:-|\u2013|\u2014|to)\s*"
    r"(?P<end>(?:[A-Za-z]{3,9}\.?\s+\d{4})|(?:\d{1,2}/\d{4})|(?:\d{4})|(?:present|current))",
    re.IGNORECASE,
)


def extract_dates(text: str) -> list[tuple[str, str]]:
    """Find ``start - end`` date-range pairs within ``text``.

    Recognises ``Month YYYY``, ``MM/YYYY``, and bare ``YYYY`` forms on
    either side of a hyphen, en dash, em dash, or the word ``to``, plus
    ``present``/``current`` as an end marker.

    Args:
        text: Plain text to search (typically a single experience or
            education entry's text).

    Returns:
        List of raw ``(start, end)`` string pairs, in document order. Date
        parsing/coercion to ``datetime.date`` happens in ``ResumeMapper``,
        not here.
    """
    return [
        (m.group("start").strip(), m.group("end").strip())
        for m in _DATE_RANGE_RE.finditer(text)
    ]


def _ensure_scheme(url: str) -> str:
    """Prefix ``https://`` onto a scheme-less URL.

    Args:
        url: A URL that may or may not already have a scheme.

    Returns:
        The URL guaranteed to start with ``http://`` or ``https://``.
    """
    if url.lower().startswith(("http://", "https://")):
        return url
    return f"https://{url}"
