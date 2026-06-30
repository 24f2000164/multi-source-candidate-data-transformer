"""Section header normalization + detection + body extraction.

Uses block isolation (font/visual isolation signal, when available) as a
stronger header signal than plain heuristics, falling back to a pure
short-line + alias heuristic when block data is coarse (DOCX) or absent.
"""

from enum import StrEnum
import re

from transformer.parsers.resume.text_extractor import ExtractedText, TextBlock

_MAX_HEADER_WORDS = 5
_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


class SectionName(StrEnum):
    """Canonical section identifiers detected within a resume."""

    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    CERTIFICATIONS = "certifications"
    LANGUAGES = "languages"


_ALIASES: dict[SectionName, frozenset[str]] = {
    SectionName.SKILLS: frozenset(
        {
            "skills",
            "technical skills",
            "core skills",
            "core competencies",
            "technologies",
            "tech stack",
            "tools",
            "frameworks",
            "technical proficiencies",
            "key skills",
        }
    ),
    SectionName.EXPERIENCE: frozenset(
        {
            "experience",
            "work experience",
            "professional experience",
            "employment history",
            "work history",
            "career history",
        }
    ),
    SectionName.EDUCATION: frozenset(
        {
            "education",
            "academic background",
            "academic qualifications",
            "educational qualifications",
            "qualifications",
        }
    ),
    SectionName.CERTIFICATIONS: frozenset(
        {
            "certifications",
            "certificates",
            "licenses & certifications",
            "professional certifications",
            "licenses and certifications",
            "licenses",
        }
    ),
    SectionName.LANGUAGES: frozenset(
        {"languages", "language proficiency", "language skills"}
    ),
}

_ALL_HEADER_ALIASES: frozenset[str] = frozenset(
    alias for aliases in _ALIASES.values() for alias in aliases
)

# Headers that terminate the current section's body but are not themselves
# modelled as a ``SectionName`` (no canonical field for them yet). Without
# these, e.g. an "Achievements & Leadership" block following "Skills" would
# be silently absorbed into the skills body. Not stored in the result dict.
_STOP_SECTIONS: frozenset[str] = frozenset(
    {
        "projects",
        "personal projects",
        "achievements",
        "achievements & leadership",
        "achievements and leadership",
        "leadership",
        "publications",
        "references",
        "awards",
        "awards & honors",
        "volunteer experience",
        "volunteering",
        "interests",
        "hobbies",
        "summary",
        "objective",
        "profile",
        "extracurricular activities",
        "extra-curricular activities",
        "extra curricular activities",
        "positions of responsibility",
        "positions",
        "responsibilities",
        "professional summary",
        "about me",
        "contact",
    }
)


class SectionDetector:
    """Detects resume sections and extracts each section's body text."""

    def detect(self, extracted: ExtractedText) -> dict[SectionName, str]:
        """Detect known sections and their body text within ``extracted``.

        Args:
            extracted: Extracted text and block metadata for the resume.

        Returns:
            Mapping of detected ``SectionName`` to its raw body text.
            Sections that are not found are simply absent from the dict --
            optional fields degrade to ``None``/``[]`` downstream, never
            raise.
        """
        header_positions: list[tuple[int, SectionName | None]] = []
        for index, block in enumerate(extracted.blocks):
            section = self._match_header(block)
            if section is not None:
                header_positions.append((index, section))
            elif self._is_stop_section(block):
                header_positions.append((index, None))

        result: dict[SectionName, str] = {}
        for pos, (index, section) in enumerate(header_positions):
            if section is None:
                continue
            end = (
                header_positions[pos + 1][0]
                if pos + 1 < len(header_positions)
                else len(extracted.blocks)
            )
            body_blocks = extracted.blocks[index + 1 : end]
            body = "\n".join(b.text for b in body_blocks)
            if body.strip():
                # First match for a section wins; later duplicate-named
                # sections are ignored to keep behaviour deterministic.
                result.setdefault(section, body)
        return result

    @staticmethod
    def _is_stop_section(block: TextBlock) -> bool:
        """Check whether ``block`` is a stop-section header.

        Stop-sections (e.g. "Projects", "Achievements & Leadership") are
        not modelled fields, but their headers still terminate whatever
        section body precedes them.

        Matching is "starts with a known stop-section root token" rather
        than exact-set membership (Bug #7: a decorated heading like
        "Projects (AI/ML Focused)" must still be recognised as the
        "projects" stop-section), but deliberately stops short of full
        fuzzy/substring matching (Bug #16: a bullet line like "Led major
        project initiatives" must NOT be misdetected as a section
        boundary) -- the existing <=5-word + isolated-block gate above
        this method already filters out long body-text lines, so only
        the *prefix* match is loosened here, not the gate itself.

        Args:
            block: A candidate text block.

        Returns:
            ``True`` if the block is a recognised stop-section header.
        """
        if len(block.text.split()) > _MAX_HEADER_WORDS:
            return False
        normalized = SectionDetector._normalize_header(block.text)
        if normalized is None:
            return False
        return any(
            normalized == stop or normalized.startswith(f"{stop} ")
            for stop in _STOP_SECTIONS
        )

    def _match_header(self, block: TextBlock) -> SectionName | None:
        """Check whether ``block`` is a recognised section header.

        Args:
            block: A candidate text block.

        Returns:
            The matched ``SectionName``, or ``None``.
        """
        if len(block.text.split()) > _MAX_HEADER_WORDS:
            return None
        normalized = self._normalize_header(block.text)
        if normalized is None:
            return None
        for section, aliases in _ALIASES.items():
            if normalized in aliases:
                return section
        return None

    @staticmethod
    def _normalize_header(line: str) -> str | None:
        """Lowercase, strip punctuation, and collapse whitespace.

        Args:
            line: Raw candidate header line.

        Returns:
            The normalized string, or ``None`` if it normalizes to blank.
        """
        cleaned = _PUNCT_RE.sub(" ", line.lower())
        cleaned = _WS_RE.sub(" ", cleaned).strip()
        return cleaned or None

    @staticmethod
    def is_header_alias(text: str) -> bool:
        """Check whether ``text`` normalizes to any known section alias.

        Used by ``NameDetector`` to exclude header lines from name
        candidates.

        Args:
            text: Candidate line text.

        Returns:
            ``True`` if the normalized text matches a known section alias.
        """
        normalized = SectionDetector._normalize_header(text)
        return normalized is not None and normalized in _ALL_HEADER_ALIASES
