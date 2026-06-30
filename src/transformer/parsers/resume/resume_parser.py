"""Resume parser: PDF/DOCX -> Canonical Candidate Model.

Orchestrator only: validate file -> extract text -> detect name -> detect
sections -> run field extractors -> assemble ``ExtractedResumeData`` -> map.
Deterministic and stateless -- safe to share across threads. No OCR, no
LLMs, no machine learning; PyMuPDF/python-docx/regex only.
"""

import logging
from pathlib import Path
import re

from transformer.models import Candidate
from transformer.parsers.base_parser import BaseParser
from transformer.parsers.exceptions import MappingError, UnsupportedFormatError
from transformer.parsers.file_validator import FileValidator
from transformer.parsers.parser_config import ParserConfig
from transformer.parsers.resume import extractors
from transformer.parsers.resume.extracted_data import (
    ExtractedResumeData,
    RawCertificationEntry,
    RawEducationEntry,
    RawExperienceEntry,
)
from transformer.parsers.resume.name_detector import NameDetector
from transformer.parsers.resume.resume_mapper import ResumeMapper
from transformer.parsers.resume.section_detector import SectionDetector, SectionName
from transformer.parsers.resume.text_extractor import ExtractedText, TextExtractor

logger = logging.getLogger(__name__)

_RESUME_ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx"})


class ResumeParser(BaseParser):
    """Parses PDF/DOCX resume files into validated Candidate models."""

    def __init__(
        self,
        file_validator: FileValidator | None = None,
        text_extractor: TextExtractor | None = None,
        section_detector: SectionDetector | None = None,
        name_detector: NameDetector | None = None,
        mapper: ResumeMapper | None = None,
        config: ParserConfig | None = None,
    ) -> None:
        """Initialise the resume parser with its collaborators.

        Args:
            file_validator: Validates the source file before parsing.
            text_extractor: Extracts plain text + blocks from PDF/DOCX.
            section_detector: Detects resume sections and their bodies.
            name_detector: Detects the candidate's name via priority
                strategy.
            mapper: Maps extracted data to the canonical model.
            config: Tunable parser configuration.
        """
        self._file_validator = file_validator or FileValidator()
        self._text_extractor = text_extractor or TextExtractor()
        self._section_detector = section_detector or SectionDetector()
        self._name_detector = name_detector or NameDetector()
        self._mapper = mapper or ResumeMapper()
        self._config = config or ParserConfig()

    def parse(self, source: Path) -> Candidate:
        """Parse a PDF/DOCX resume file into a validated ``Candidate``.

        Args:
            source: Filesystem path to the resume file.

        Returns:
            A fully validated ``Candidate`` instance.

        Raises:
            FileReadError: If the file is missing, unreadable, or exceeds
                the configured size limit.
            UnsupportedFormatError: If the file extension is not ``.pdf``
                or ``.docx``.
            CorruptedFileError: If the file cannot be opened by its
                declared format (corrupted, encrypted, or an
                extension/content mismatch).
            TextExtractionError: If no usable text could be extracted
                (e.g. an image-only PDF).
            MappingError: If a name cannot be detected, or a detected
                nested entry is invalid.
        """
        logger.info("resume_parse_started", extra={"path": str(source)})

        self._validate_resume_file(source)

        extracted = self._text_extractor.extract(source)
        logger.info("resume_text_extracted", extra={"path": str(source)})

        data = self._assemble(extracted)

        try:
            candidate = self._mapper.map_candidate(data)
        except MappingError:
            logger.warning("resume_mapping_failed", extra={"path": str(source)})
            raise

        logger.info(
            "resume_parse_completed",
            extra={"path": str(source), "candidate_id": str(candidate.id)},
        )
        return candidate

    def _validate_resume_file(self, source: Path) -> None:
        """Validate the source file, including the resume-specific extension set.

        Args:
            source: Filesystem path to the resume file.

        Raises:
            FileReadError: If the file fails generic file validation.
            UnsupportedFormatError: If the extension is not ``.pdf``/``.docx``.
        """
        suffix = source.suffix.lower()
        if suffix not in _RESUME_ALLOWED_EXTENSIONS:
            raise UnsupportedFormatError(
                f"Unsupported resume file extension: {suffix or '(none)'}"
            )
        self._file_validator.validate(
            source, self._config, allowed_extensions=_RESUME_ALLOWED_EXTENSIONS
        )

    def _assemble(self, extracted: ExtractedText) -> ExtractedResumeData:
        """Run all detectors/extractors and assemble the typed intermediate.

        Pure orchestration: delegates every decision to ``NameDetector``,
        ``SectionDetector``, and the pure functions in ``extractors`` --
        this method only wires their outputs together.

        Args:
            extracted: Extracted text and block metadata for the resume.

        Returns:
            The assembled ``ExtractedResumeData``.
        """
        name = self._name_detector.detect(extracted)
        sections = self._section_detector.detect(extracted)

        first_name, last_name = name if name is not None else (None, None)

        skills_text = sections.get(SectionName.SKILLS, "")
        languages_text = sections.get(SectionName.LANGUAGES, "")
        certifications_text = sections.get(SectionName.CERTIFICATIONS, "")
        header_text = self._extract_header_text(extracted)

        return ExtractedResumeData(
            first_name=first_name,
            last_name=last_name,
            email=extractors.extract_email(extracted.plain_text),
            phone=extractors.extract_phone(extracted.plain_text),
            location=extractors.extract_location(header_text),
            linkedin_url=extractors.extract_linkedin_url(extracted.plain_text),
            github_url=extractors.extract_github_url(extracted.plain_text),
            skills=extractors.extract_list_items(skills_text) if skills_text else [],
            languages=(
                extractors.extract_languages(languages_text) if languages_text else []
            ),
            experience_entries=self._build_experience_entries(
                sections.get(SectionName.EXPERIENCE)
            ),
            education_entries=self._build_education_entries(
                sections.get(SectionName.EDUCATION)
            ),
            certifications=self._build_certification_entries(certifications_text),
        )

    @staticmethod
    def _extract_header_text(extracted: ExtractedText) -> str:
        """Return only the document text preceding the first section header.

        Location detection must never read from inside a section body
        (e.g. an Experience entry's "Company   City, Country" line) -- it
        should only look at the resume's header/contact block. This finds
        the first line that is a recognised section-header alias and
        returns everything before it; if no header is found, the whole
        document is returned (preserves prior behaviour for resumes with
        no detectable sections at all).

        Args:
            extracted: Extracted text and block metadata for the resume.

        Returns:
            The plain text of the document up to (but excluding) the
            first detected section header line.
        """
        lines = extracted.plain_text.splitlines()
        for index, line in enumerate(lines):
            if SectionDetector.is_header_alias(line.strip()):
                return "\n".join(lines[:index])
        return extracted.plain_text

    @staticmethod
    def _build_certification_entries(
        section_text: str | None,
    ) -> list[RawCertificationEntry]:
        """Build raw certification entries from a section body.

        Args:
            section_text: Raw body text of the Certifications section, if
                detected.

        Returns:
            List of raw certification entries; empty if no section found.
        """
        if not section_text:
            return []
        return [
            RawCertificationEntry(name=name)
            for name in extractors.extract_certifications(section_text)
        ]

    _BULLET_PREFIXES = ("•", "-", "*", "\u2013", "\u2014")

    @classmethod
    def _is_bullet(cls, line: str) -> bool:
        """Check whether ``line`` starts with a bullet marker.

        Args:
            line: A single stripped line of text.

        Returns:
            ``True`` if the line begins with a recognised bullet marker.
        """
        return line.startswith(cls._BULLET_PREFIXES)

    @classmethod
    def _strip_bullet(cls, line: str) -> str:
        """Remove a leading bullet marker and surrounding whitespace.

        Args:
            line: A single stripped line of text.

        Returns:
            The line with its leading bullet marker removed.
        """
        return line.lstrip("".join(cls._BULLET_PREFIXES)).strip()

    @classmethod
    def _build_experience_entries(
        cls,
        section_text: str | None,
    ) -> list[RawExperienceEntry]:
        """Build raw experience entries from a section body.

        Two independent, non-interacting code paths (Bug #15: heuristics
        from one flow are never reused by the other, to avoid e.g. the
        newline-flow's location-comma heuristic misfiring on pipe
        segments):

        1. **Pipe-delimited single-line flow**: a line containing ``|``
           (e.g. ``"Acme Corp | Engineer | Jan 2022 - Present"``) is split
           on ``|`` and each segment is classified independently as a
           date-range, else treated as company/title in encounter order.
           Bullet lines immediately following the pipe-line become that
           entry's description.
        2. **Newline multi-line flow** (unchanged from the original
           design): groups ``(header lines..., date line, bullet
           lines...)`` runs across multiple lines.

        A line is routed to the pipe flow if and only if it contains
        ``|`` AND a date range is found among its pipe-segments; this
        keeps an accidental ``|`` in unrelated text from being misrouted.

        Args:
            section_text: Raw body text of the Experience section, if
                detected.

        Returns:
            List of raw experience entries; empty if no section/dates
            found.
        """
        if not section_text:
            return []
        lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]

        entries: list[RawExperienceEntry] = []
        pending_newline_lines: list[str] = []

        def flush_newline_lines() -> None:
            if pending_newline_lines:
                entries.extend(
                    cls._build_experience_entries_newline_flow(pending_newline_lines)
                )
                pending_newline_lines.clear()

        i, n = 0, len(lines)
        while i < n:
            line = lines[i]
            pipe_entry = cls._try_build_pipe_experience_entry(line)
            if pipe_entry is not None:
                flush_newline_lines()
                i += 1
                # Bullet lines immediately following a pipe entry's header
                # line belong to that entry's description -- the same
                # role they play in the newline-flow, just attached here
                # since the pipe flow has no separate "date line" step to
                # transition out of.
                desc_lines: list[str] = []
                while i < n and cls._is_bullet(lines[i]):
                    desc_lines.append(cls._strip_bullet(lines[i]))
                    i += 1
                if desc_lines:
                    pipe_entry = pipe_entry.model_copy(
                        update={"description": "\n".join(desc_lines)}
                    )
                entries.append(pipe_entry)
            else:
                pending_newline_lines.append(line)
                i += 1
        flush_newline_lines()
        return entries

    @classmethod
    def _try_build_pipe_experience_entry(cls, line: str) -> RawExperienceEntry | None:
        """Build a single experience entry from a pipe-delimited line.

        Args:
            line: A candidate line, possibly pipe-delimited.

        Returns:
            A ``RawExperienceEntry`` if ``line`` contains ``|`` and at
            least one pipe-segment is a date range, otherwise ``None``
            (so the caller falls back to the newline-flow).
        """
        if "|" not in line:
            return None
        segments = [seg.strip() for seg in line.split("|") if seg.strip()]
        if not segments:
            return None

        date_segment_index: int | None = None
        dates: list[tuple[str, str]] = []
        for index, segment in enumerate(segments):
            found = extractors.extract_dates(segment)
            if found:
                date_segment_index = index
                dates = found
                break
        if date_segment_index is None:
            return None

        non_date_segments = [
            seg for i, seg in enumerate(segments) if i != date_segment_index
        ]
        if not non_date_segments:
            company = title = None
        elif len(non_date_segments) == 1:
            company = title = non_date_segments[0]
        else:
            company = non_date_segments[0]
            title = " ".join(non_date_segments[1:])

        start, end = dates[0]
        return RawExperienceEntry(
            company=company,
            title=title,
            start_date=start,
            end_date=end,
            description=None,
        )

    @classmethod
    def _build_experience_entries_newline_flow(
        cls,
        lines: list[str],
    ) -> list[RawExperienceEntry]:
        """Build raw experience entries from non-pipe, multi-line runs.

        Each run is ``(header lines..., date line OR same-line
        text+date, bullet lines...)``. Three cases for the line(s) that
        carry the date:

        1. **Same-line mixed text + date** (e.g. ``"Software Engineer,
           Google — Jan 2022 – Present"``): the date substring is located
           and stripped out of the line first (rather than assuming a
           date always occupies its own line), and the remaining text is
           classified into title/company via
           ``_split_title_company_segment``.
        2. **Pure date-only line** preceded by header line(s): the date
           line itself contributes nothing to company/title; the
           preceding header line(s) are classified the same way a
           same-line match would be -- a single header line is checked
           for an embedded separator (comma/dash/pipe) via
           ``_split_title_company_segment``; if no separator is present
           and the line is therefore ambiguous (Bug: a lone ``"Software
           Engineer"`` header can not be deterministically split into a
           distinct company and title), the entry is skipped rather than
           hallucinating ``company = title`` from the same string.
        3. **Multiple header lines**: first line(s) are ``company``, last
           line is ``title`` (unchanged prior behaviour) -- this case is
           unambiguous since two physically distinct lines are already
           given.

        A trailing ``City, Region``-shaped fragment is stripped from a
        company candidate before it is used, so it is never blended into
        ``company``/``title`` (location is contact-level data, not
        company metadata).

        Args:
            lines: Stripped, non-empty lines that were not routed to the
                pipe-delimited flow.

        Returns:
            List of raw experience entries; empty if no dates found.
            Entries whose company/title cannot be deterministically
            recovered are omitted rather than guessed.
        """
        entries: list[RawExperienceEntry] = []
        i, n = 0, len(lines)
        while i < n:
            header_lines: list[str] = []
            same_line_date: tuple[str, str] | None = None
            same_line_remainder: str | None = None

            while i < n:
                line = lines[i]
                if cls._is_bullet(line):
                    i += 1
                    continue
                span = extractors.extract_date_span(line)
                if span is not None:
                    start_off, end_off, start, end = span
                    remainder = (line[:start_off] + line[end_off:]).strip(" ,-—–|")
                    same_line_date = (start, end)
                    same_line_remainder = remainder or None
                    i += 1
                    break
                header_lines.append(line)
                i += 1

            if same_line_date is None:
                # No date found before running out of lines in this run;
                # nothing left to build an entry from.
                break

            start, end = same_line_date

            desc_lines: list[str] = []
            while i < n and cls._is_bullet(lines[i]):
                desc_lines.append(cls._strip_bullet(lines[i]))
                i += 1

            company, title = cls._resolve_company_title(
                header_lines, same_line_remainder
            )
            if company is None or title is None:
                # Bug #4: never hallucinate company == title from a single
                # ambiguous header line -- skip rather than guess.
                continue

            entries.append(
                RawExperienceEntry(
                    company=company,
                    title=title,
                    start_date=start,
                    end_date=end,
                    description="\n".join(desc_lines) if desc_lines else None,
                )
            )
        return entries

    _TITLE_COMPANY_SEPARATORS = (",", "\u2014", "\u2013", "-", "|")

    @classmethod
    def _split_title_company_segment(cls, segment: str) -> tuple[str, str] | None:
        """Split a single ``"Title, Company"``-shaped segment.

        Supports ``Title, Company``, ``Title - Company``, ``Title |
        Company``, and em/en-dash variants. The first recognised
        separator found determines the split point.

        Args:
            segment: A single line/remainder believed to contain both a
                job title and a company name, with any date substring
                already removed.

        Returns:
            A ``(company, title)`` tuple, or ``None`` if no recognised
            separator is present (the segment is ambiguous and must not
            be guessed at).
        """
        for sep in cls._TITLE_COMPANY_SEPARATORS:
            if sep in segment:
                left, _, right = segment.partition(sep)
                left, right = left.strip(), right.strip()
                if left and right:
                    return right, left
        return None

    @classmethod
    def _resolve_company_title(
        cls,
        header_lines: list[str],
        same_line_remainder: str | None,
    ) -> tuple[str | None, str | None]:
        """Resolve ``(company, title)`` from the header lines of one entry.

        Args:
            header_lines: Zero or more lines preceding the date line/
                same-line date match.
            same_line_remainder: The non-date text remaining on the same
                line as the matched date, if the date was found embedded
                in a line with other text; ``None`` if the date occupied
                its own line.

        Returns:
            A ``(company, title)`` tuple. Either element may be ``None``
            if no deterministic split could be found -- callers must
            treat a ``None`` result as "skip this entry", never as
            license to fall back to duplicating a single string into
            both fields.
        """
        if same_line_remainder is not None:
            cleaned_remainder = cls._strip_trailing_location(same_line_remainder)
            split = cls._split_title_company_segment(cleaned_remainder)
            if split is not None:
                return split
            if header_lines:
                # The date-bearing line's remainder (e.g. "Senior
                # Software Engineer") has no embedded separator, but a
                # distinct preceding header line already exists -- the
                # two physically separate lines unambiguously give
                # company (header line(s)) and title (remainder), the
                # same way the multi-header-line case works below.
                company = cls._strip_trailing_location(" ".join(header_lines))
                return (company or None), (cleaned_remainder or None)
            # A bare date with no separator-bearing remainder and no
            # preceding header lines at all -- nothing to recover.
            return None, None

        if not header_lines:
            return None, None

        if len(header_lines) == 1:
            cleaned_line = cls._strip_trailing_location(header_lines[0])
            split = cls._split_title_company_segment(cleaned_line)
            if split is not None:
                return split
            # A single, separator-less header line (e.g. just "Software
            # Engineer", or "Microsoft" after its trailing location was
            # stripped) cannot be deterministically split into a distinct
            # company and title -- Bug #4: do not duplicate it into both
            # fields.
            return None, None

        company = cls._strip_trailing_location(" ".join(header_lines[:-1]))
        title = header_lines[-1]
        return company, title

    _TRAILING_LOCATION_RE = re.compile(
        r"\s{2,}[A-Z][A-Za-z.\s]+,\s*[A-Za-z.\s]+$"
    )

    @classmethod
    def _strip_trailing_location(cls, company: str) -> str:
        """Strip a trailing ``City, Region``-shaped fragment from a company
        candidate.

        Resumes commonly lay out ``"Company                City, Country"``
        on one line, separated by multiple spaces/a tab. That trailing
        fragment is location metadata, not part of the company name, and
        must never be blended into ``company`` or leak into
        ``contact.location`` via the experience section.

        Args:
            company: A candidate company string, possibly with a trailing
                location fragment.

        Returns:
            ``company`` with any trailing ``"  City, Region"``-shaped
            fragment removed; unchanged if no such fragment is found.
        """
        match = cls._TRAILING_LOCATION_RE.search(company)
        if match is None:
            return company.strip()
        return company[: match.start()].strip()

    _DEGREE_KEYWORDS = (
        "bachelor",
        "master",
        "associate",
        "diploma",
        "phd",
        "doctor",
        "b.tech",
        "btech",
        "b.sc",
        "bsc",
        "b.s.",
        " bs ",
        "b.e.",
        " be ",
        "b.a.",
        " ba ",
        "m.tech",
        "mtech",
        "m.sc",
        "msc",
        "m.s.",
        " ms ",
        "m.a.",
        " ma ",
        "mba",
        "mca",
        "bca",
    )

    _DEGREE_FIELD_SEPARATOR_RE = re.compile(r"\s+in\s+|\s*[\u2013\u2014-]\s*")

    @classmethod
    def _split_degree_field(cls, line: str) -> tuple[str, str | None]:
        """Split a cleaned degree line into ``(degree, field_of_study)``.

        Splits on the first occurrence of ``" in "`` or a hyphen/en-dash/
        em-dash separator, whichever appears first (Bug #11: dash-style
        separators such as ``"BS - Data Science"`` (en-dash or hyphen) are
        just as valid as ``" in "``-style ones).

        Args:
            line: A degree-line with parenthetical abbreviations already
                stripped.

        Returns:
            A ``(degree, field_of_study)`` tuple; ``field_of_study`` is
            ``None`` if no separator was found.
        """
        match = cls._DEGREE_FIELD_SEPARATOR_RE.search(line)
        if not match:
            return line.strip(), None
        degree_part = line[: match.start()].strip()
        field_part = line[match.end() :].strip()
        return degree_part, (field_part or None)

    _SECONDARY_EDUCATION_DENYLIST = (
        "school",
        "senior secondary",
        "secondary school",
        "high school",
        "class 10",
        "class 12",
        "class x",
        "class xii",
        "cbse",
        "icse",
        "10th",
        "12th",
    )

    _GPA_RE = re.compile(
        r"(?:cgpa|gpa)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:/\s*(\d+(?:\.\d+)?))?",
        re.IGNORECASE,
    )
    _PERCENTAGE_RE = re.compile(r"\d{1,3}(?:\.\d+)?\s*%")

    @classmethod
    def _looks_like_degree_line(cls, line: str) -> bool:
        """Check whether ``line`` contains a recognised degree keyword.

        Includes both spelled-out forms (``"bachelor"``) and common
        abbreviated forms (``"B.Tech"``, ``"BS"``, ``"M.Sc"``, ...), so a
        degree line is not silently dropped just because the resume uses
        an abbreviation rather than the spelled-out word.

        Args:
            line: A single education-section line.

        Returns:
            ``True`` if a degree keyword is present.
        """
        padded = f" {line.lower()} "
        return any(kw in padded for kw in cls._DEGREE_KEYWORDS)

    @classmethod
    def _is_secondary_education_line(cls, line: str) -> bool:
        """Check whether ``line`` refers to school-level (non-degree) education.

        Args:
            line: A single education-section line.

        Returns:
            ``True`` if the line mentions school/Class 10/Class 12/board
            exam tokens, which should never become a degree-level entry
            even if a degree keyword coincidentally appears nearby.
        """
        lowered = line.lower()
        return any(token in lowered for token in cls._SECONDARY_EDUCATION_DENYLIST)

    @classmethod
    def _extract_gpa(cls, line: str) -> float | None:
        """Extract a GPA/CGPA value from a line, normalised to a 0.0-4.0 scale.

        Recognises ``"CGPA: 8.55 / 10"``, ``"GPA 3.8"``, ``"CGPA-9.1/10"``.
        When a denominator is present (e.g. ``"/10"``) the value is
        rescaled to a 4.0 scale; without a denominator the value is
        assumed to already be on a 4.0 scale.

        Args:
            line: A single education-section line.

        Returns:
            The normalised GPA as a float in ``[0.0, 4.0]``, or ``None``
            if no GPA pattern is found or the result would be out of
            range.
        """
        match = cls._GPA_RE.search(line)
        if not match:
            return None
        value = float(match.group(1))
        denominator = float(match.group(2)) if match.group(2) else 4.0
        if denominator <= 0:
            return None
        normalised = (value / denominator) * 4.0
        if not (0.0 <= normalised <= 4.0):
            return None
        return round(normalised, 2)

    @classmethod
    def _is_institution_candidate_shaped(cls, line: str) -> bool:
        """Check whether ``line`` is shaped like an institution name.

        Rejects lines that are actually dates, GPA/CGPA figures, or
        percentage/grade figures -- these must never become a spurious
        new "institution" entry (Bug #6); they are routed to date/GPA
        extraction instead (Bug #6a).

        Args:
            line: A candidate line for starting a new education entry.

        Returns:
            ``True`` if the line is plausibly an institution name.
        """
        if extractors.extract_dates(line):
            return False
        if cls._GPA_RE.search(line):
            return False
        return not cls._PERCENTAGE_RE.search(line)

    @classmethod
    def _build_education_entries(
        cls,
        section_text: str | None,
    ) -> list[RawEducationEntry]:
        """Build raw education entries from a section body.

        Groups consecutive non-blank lines per entry. The first
        institution-shaped line starts a new entry (parenthetical
        abbreviations like ``"(IIT)"`` are stripped); a later line
        containing a recognised degree keyword (spelled-out or
        abbreviated, e.g. ``"B.Tech"``, ``"BS"``) is split into ``degree``
        and ``field_of_study`` using either ``" in "`` or a dash/en-dash
        separator. Date-range lines are assigned to the current entry's
        start/end date rather than becoming a new institution. GPA/CGPA
        lines are parsed and normalised onto the entry. Lines that are
        date-shaped, GPA-shaped, percentage-shaped, or refer to
        school/secondary-level education never start a new entry.

        Args:
            section_text: Raw body text of the Education section, if
                detected.

        Returns:
            List of raw education entries; empty if no section found.
        """
        if not section_text:
            return []
        abbrev_re = re.compile(r"\s*\([^()]{1,20}\)")
        lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]

        entries: list[RawEducationEntry] = []
        institution: str | None = None
        degree: str | None = None
        field_of_study: str | None = None
        start_date: str | None = None
        end_date: str | None = None
        gpa: float | None = None
        skip_entry = False

        def flush() -> None:
            if institution is not None and degree is not None and not skip_entry:
                entries.append(
                    RawEducationEntry(
                        institution=institution,
                        degree=degree,
                        field_of_study=field_of_study,
                        start_date=start_date,
                        end_date=end_date,
                        gpa=gpa,
                    )
                )

        for line in lines:
            dates = extractors.extract_dates(line)
            gpa_value = cls._extract_gpa(line)

            if dates:
                # Bug #6a: assign to the pending entry, never treat as a
                # new institution candidate.
                start_date, end_date = dates[0]
                continue

            if gpa_value is not None:
                gpa = gpa_value
                continue

            if cls._looks_like_degree_line(
                line
            ) and not cls._is_secondary_education_line(line):
                cleaned = abbrev_re.sub("", line)
                degree_part, field_part = cls._split_degree_field(cleaned)
                degree = degree_part
                field_of_study = field_part
            elif (
                "," in line
                and len(line.split()) <= 4
                and institution is not None
                and degree is None
            ):
                # Location line following an institution that hasn't yet
                # received its degree line (e.g. "Chennai, India") -- not
                # modelled. Guarded by `degree is None` so this never
                # fires on a comma-bearing *institution* line itself (Bug
                # #15: "MIT, USA" must still be able to start a new entry).
                continue
            elif cls._PERCENTAGE_RE.search(line):
                # Grade percentage line not already caught by GPA pattern
                # (e.g. "CBSE Class 12: 90%") -- never starts a new entry.
                continue
            elif not cls._is_institution_candidate_shaped(line):
                # Defensive: date/GPA/percentage-shaped line that slipped
                # past the earlier checks -- still never a new institution.
                continue
            else:
                # A new institution-shaped line starts a new entry.
                flush()
                candidate_institution = abbrev_re.sub("", line).strip()
                skip_entry = cls._is_secondary_education_line(candidate_institution)
                institution = candidate_institution
                degree = None
                field_of_study = None
                start_date = None
                end_date = None
                gpa = None
        flush()
        return entries