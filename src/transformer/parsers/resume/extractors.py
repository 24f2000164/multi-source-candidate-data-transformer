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

    Email local-parts are stripped first so phone-shaped digit runs inside
    an email address (e.g. ``24f2000164@...``) are never mistaken for a
    phone number.

    Args:
        text: Plain text to search.

    Returns:
        The first matched phone number with at least
        ``_MIN_PHONE_DIGITS`` digits, or ``None`` if no match.
    """
    text_without_emails = _EMAIL_RE.sub(" ", text)
    for match in _PHONE_RE.finditer(text_without_emails):
        digits = re.sub(r"\D", "", match.group(0))
        if len(digits) >= _MIN_PHONE_DIGITS:
            return match.group(0).strip()
    return None



def extract_date_span(text: str) -> tuple[int, int, str, str] | None:
    """Find the first date-range match in ``text`` and return its span.
 
    Unlike ``extract_dates``, this also returns the character offsets of
    the match so a caller can remove the date substring from a line that
    mixes a date with other text (e.g. ``"Title, Company — Jan 2022 -
    Present"``).
 
    Args:
        text: Plain text to search.
 
    Returns:
        A ``(start, end, start_date, end_date)`` tuple for the first
        match, or ``None`` if no date range is found.
    """
    match = _DATE_RANGE_RE.search(text)
    if match is None:
        return None
    return (
        match.start(),
        match.end(),
        match.group("start").strip(),
        match.group("end").strip(),
    )


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


_CATEGORY_PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z &/]{0,40}:\s+")


# Matches a lone page-number / footnote-index line: a single integer
# (optionally preceded by whitespace), nothing else. These appear in
# PDF-extracted text when the extractor picks up "1" or "2" at the
# bottom of a page that falls inside a section body.
_LONE_INTEGER_RE = re.compile(r"^\d{1,3}$")


def _join_dangling_parens(lines: list[str]) -> list[str]:
    """Merge a line whose paren block was split across a PDF page break.

    When PyMuPDF extracts text from a two-column or paginated PDF the
    content of a single parenthetical (e.g. ``"Generative AI (LangChain,
    OpenAI GPT,"`` on page 1 and ``"Whisper)"`` on page 2) may arrive as
    two separate lines.  This pass scans for an unclosed ``(`` and
    appends subsequent lines (skipping lone page-number lines) until the
    paren depth returns to zero.

    Args:
        lines: Lines already stripped of leading/trailing whitespace.

    Returns:
        Lines with split parentheticals rejoined.
    """
    result: list[str] = []
    for line in lines:
        if result and result[-1].count("(") > result[-1].count(")"):
            # Previous line has an unclosed paren -- append current to it.
            result[-1] = result[-1] + " " + line
        else:
            result.append(line)
    return result


def extract_list_items(section_text: str) -> list[str]:
    """Split a section body into discrete items (skills, languages, etc.).

    Processes line-by-line: a leading category label (e.g.
    ``"Languages: "`` in ``"Languages: Python, SQL"``) is stripped first,
    then each line is split on commas/bullets/pipes/semicolons -- but a
    comma inside balanced parentheses (e.g. ``"Ensemble Learning
    (LightGBM)"``) is treated as part of the phrase, not a separator, so
    multi-word/parenthetical skills stay intact.  Strips whitespace and
    drops empty entries while preserving order and removing duplicates
    (case-insensitive).

    Additionally:
    * Lone page-number / footnote-index lines (a bare integer such as
      ``"1"`` or ``"2"`` that the PDF extractor picked up from the bottom
      of a page) are dropped before any splitting occurs.
    * Lines whose parenthetical was split across a PDF page break are
      re-joined before splitting so ``"Generative AI (LangChain, OpenAI
      GPT,"`` + ``"Whisper)"`` produce a single item.

    Args:
        section_text: Raw text body of a section (e.g. the Skills section).

    Returns:
        Ordered, deduplicated list of trimmed item strings.
    """
    # 1. Pre-process: strip, drop lone integers, rejoin broken parens.
    raw_lines = [
        _CATEGORY_PREFIX_RE.sub("", ln.strip())
        for ln in section_text.splitlines()
    ]
    raw_lines = [ln for ln in raw_lines if ln and not _LONE_INTEGER_RE.match(ln)]
    raw_lines = _join_dangling_parens(raw_lines)

    seen: set[str] = set()
    result: list[str] = []
    for line in raw_lines:
        for item in _split_respecting_parens(line):
            item = item.strip(" \t-\u2022")
            if not item:
                continue
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
    return result


def _split_respecting_parens(line: str) -> list[str]:
    """Split ``line`` on list separators, ignoring separators inside ``()``.

    Args:
        line: A single line of text (category prefix already stripped).

    Returns:
        List of raw (untrimmed) split segments.
    """
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for char in line:
        if char == "(":
            depth += 1
            buf.append(char)
        elif char == ")":
            depth = max(0, depth - 1)
            buf.append(char)
        elif depth == 0 and char in ",•\u2022|;":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(char)
    parts.append("".join(buf))
    return parts


_DATE_RANGE_RE = re.compile(
    r"(?P<start>(?:[A-Za-z]{3,9}\.?[\s\-]+\d{4})|(?:\d{1,2}/\d{4})|(?:\d{4}))"
    r"\s*(?:-|\u2013|\u2014|to)\s*"
    r"(?P<end>(?:[A-Za-z]{3,9}\.?[\s\-]+\d{4})|(?:\d{1,2}/\d{4})|(?:\d{4})|(?:present|current))",
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


_LOCATION_LINE_RE = re.compile(r"^[A-Z][A-Za-z.\s]+,\s*[A-Z][A-Za-z.\s]+$")
_LOCATION_SEGMENT_RE = re.compile(r"^[A-Z][A-Za-z.\s]+,\s*[A-Za-z.\s]+$")
_PHONE_LIKE_RE = re.compile(r"\d{3}")


def extract_location(text: str) -> str | None:
    """Find the candidate's location (``"City, Region"``-style) in ``text``.

    Looks at the header lines (first few lines, and ``|``-delimited
    contact-line segments) for a ``"City, Region"`` shaped fragment that
    is not an email, phone number, or URL.

    Args:
        text: Plain text to search (typically the whole resume text).

    Returns:
        The matched location string, or ``None`` if no match.
    """
    candidates: list[str] = []
    for line in text.splitlines()[:6]:
        for segment in line.split("|"):
            segment = segment.strip()
            candidates.append(segment)
        candidates.append(line.strip())

    for segment in candidates:
        if not segment or "@" in segment:
            continue
        lowered = segment.lower()
        if "linkedin" in lowered or "github" in lowered or "http" in lowered:
            continue
        if _PHONE_LIKE_RE.search(segment):
            continue
        if _LOCATION_SEGMENT_RE.match(segment):
            return segment
    return None


_PROFICIENCY_RE = re.compile(
    r"\s*[\(\-\u2013]\s*(?:native|fluent|proficient|intermediate|beginner|"
    r"basic|advanced|professional|conversational|elementary|full "
    r"professional|limited working|c1|c2|b1|b2|a1|a2)[\)]?\s*$",
    re.IGNORECASE,
)


def extract_languages(section_text: str) -> list[str]:
    """Extract spoken languages, dropping trailing proficiency markers.

    Reuses :func:`extract_list_items` for splitting, then strips a
    trailing proficiency qualifier such as ``"(Native)"`` or
    ``"- Fluent"`` from each item (e.g. ``"English (Native)"`` ->
    ``"English"``).

    Args:
        section_text: Raw text body of the Languages section.

    Returns:
        Ordered, deduplicated list of language names without proficiency
        levels.
    """
    items = extract_list_items(section_text)
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = _PROFICIENCY_RE.sub("", item).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def extract_certifications(section_text: str) -> list[str]:
    """Extract certification names from a Certifications section body.

    Splits the section into discrete items the same way
    :func:`extract_list_items` does (one per line/bullet/comma-separated
    entry), without further heuristics -- issuer/date parsing is left to
    callers that need it.

    Args:
        section_text: Raw text body of the Certifications section.

    Returns:
        Ordered, deduplicated list of certification name strings.
    """
    return extract_list_items(section_text)
