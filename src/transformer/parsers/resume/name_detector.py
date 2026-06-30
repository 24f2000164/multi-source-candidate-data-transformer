"""Priority-strategy name detection, independent of section detection.

Tries each strategy in order; first success wins:
1. Largest/top-most heading (first block on page 1, when block data is
   available and looks name-like).
2. First valid candidate line among the first few non-empty lines.
3. No match -> ``None`` (caller fails gracefully).
"""

import re

from transformer.parsers.resume.extractors import (
    extract_email,
    extract_linkedin_url,
    extract_phone,
)
from transformer.parsers.resume.section_detector import SectionDetector
from transformer.parsers.resume.text_extractor import ExtractedText

_MAX_NAME_WORDS = 4
_MIN_NAME_WORDS = 2
_SCAN_LINE_LIMIT = 5
_NAME_WORD_RE = re.compile(r"^[^\W\d_][^\W\d_'\-]*$", re.UNICODE)

# Section headers and school/board labels that must never be mistaken for a
# candidate name, even when they happen to be 2-4 capitalised words (e.g.
# "Class XII", "Higher Secondary"). Checked in addition to
# ``SectionDetector.is_header_alias`` (which only covers the canonical
# section names), since school-label lines like "Class XII" or "CBSE" are
# not section headers at all -- they are body content that a naive
# word-count/capitalisation heuristic would otherwise accept as a name.
_NAME_DENYLIST = frozenset(
    {
        "education",
        "experience",
        "projects",
        "skills",
        "summary",
        "certifications",
        "languages",
        "achievements",
        "class x",
        "class xii",
        "cbse",
        "icse",
        "higher secondary",
        "secondary",
    }
)


def _is_denylisted(line: str) -> bool:
    """Check whether ``line`` is a known section header or school label.

    Args:
        line: Candidate line of text.

    Returns:
        ``True`` if the lower-cased, whitespace-collapsed line exactly
        matches a denylisted term.
    """
    normalized = " ".join(line.lower().split())
    return normalized in _NAME_DENYLIST


class NameDetector:
    """Detects a candidate's first and last name from extracted resume text."""

    def detect(self, extracted: ExtractedText) -> tuple[str, str] | None:
        """Detect a (first_name, last_name) pair using priority strategies.

        Args:
            extracted: Extracted text and block metadata for the resume.

        Returns:
            A ``(first_name, last_name)`` tuple, or ``None`` if no strategy
            found a confident match.
        """
        top_block_result = self._top_block_heuristic(extracted)
        if top_block_result is not None:
            return top_block_result

        return self._proximity_heuristic(extracted)

    def _top_block_heuristic(self, extracted: ExtractedText) -> tuple[str, str] | None:
        """Use the first block on page 1 as a name candidate, if plausible.

        Args:
            extracted: Extracted text and block metadata.

        Returns:
            A name tuple if the first page-1 block looks like a name,
            otherwise ``None``.
        """
        page_one_blocks = [b for b in extracted.blocks if b.page_index == 0]
        if not page_one_blocks:
            return None
        first = min(page_one_blocks, key=lambda b: b.order)
        if not first.is_isolated:
            return None
        return self._as_name(first.text)

    def _proximity_heuristic(self, extracted: ExtractedText) -> tuple[str, str] | None:
        """Scan the first few non-empty lines for a name-shaped candidate.

        Args:
            extracted: Extracted text and block metadata.

        Returns:
            A name tuple from the first qualifying line, or ``None``.
        """
        lines = [line.strip() for line in extracted.plain_text.splitlines()]
        candidates = [line for line in lines if line][:_SCAN_LINE_LIMIT]
        for line in candidates:
            if SectionDetector.is_header_alias(line):
                continue
            if extract_email(line) or extract_phone(line) or extract_linkedin_url(line):
                continue
            name = self._as_name(line)
            if name is not None:
                return name
        return None

    @staticmethod
    def _as_name(line: str) -> tuple[str, str] | None:
        """Check whether ``line`` looks like a 2-4 word capitalised name.

        Args:
            line: Candidate line of text.

        Returns:
            A ``(first_name, last_name)`` tuple if ``line`` qualifies,
            otherwise ``None``.
        """
        words = line.split()
        if not (_MIN_NAME_WORDS <= len(words) <= _MAX_NAME_WORDS):
            return None
        if any("@" in w or w.isdigit() for w in words):
            return None
        if not all(_NAME_WORD_RE.match(w) for w in words):
            return None
        if not all(w[0].isupper() for w in words):
            return None
        if _is_denylisted(line):
            return None
        return words[0], " ".join(words[1:])
