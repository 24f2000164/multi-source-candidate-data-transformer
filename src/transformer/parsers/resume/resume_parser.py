"""Resume parser: PDF/DOCX -> Canonical Candidate Model.

Orchestrator only: validate file -> extract text -> detect name -> detect
sections -> run field extractors -> assemble ``ExtractedResumeData`` -> map.
Deterministic and stateless -- safe to share across threads. No OCR, no
LLMs, no machine learning; PyMuPDF/python-docx/regex only.
"""

import logging
from pathlib import Path

from transformer.models import Candidate
from transformer.parsers.base_parser import BaseParser
from transformer.parsers.exceptions import MappingError, UnsupportedFormatError
from transformer.parsers.file_validator import FileValidator
from transformer.parsers.parser_config import ParserConfig
from transformer.parsers.resume import extractors
from transformer.parsers.resume.extracted_data import (
    ExtractedResumeData,
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

        return ExtractedResumeData(
            first_name=first_name,
            last_name=last_name,
            email=extractors.extract_email(extracted.plain_text),
            phone=extractors.extract_phone(extracted.plain_text),
            linkedin_url=extractors.extract_linkedin_url(extracted.plain_text),
            github_url=extractors.extract_github_url(extracted.plain_text),
            skills=extractors.extract_list_items(skills_text) if skills_text else [],
            languages=(
                extractors.extract_list_items(languages_text) if languages_text else []
            ),
            experience_entries=self._build_experience_entries(
                sections.get(SectionName.EXPERIENCE)
            ),
            education_entries=[],
            certifications=[],
        )

    @staticmethod
    def _build_experience_entries(
        section_text: str | None,
    ) -> list[RawExperienceEntry]:
        """Build best-effort raw experience entries from a section body.

        One entry per non-empty line containing a detected date range; the
        line is used as both a free-text description and the source of the
        date range. Known limitation: company/title are not separately
        disambiguated from a single text line without further structural
        signal (documented, not silently broken -- see Sprint 03 plan
        Section 8).

        Args:
            section_text: Raw body text of the Experience section, if
                detected.

        Returns:
            List of raw experience entries; empty if no section/dates
            found.
        """
        if not section_text:
            return []
        entries: list[RawExperienceEntry] = []
        for line in section_text.splitlines():
            line = line.strip()
            if not line:
                continue
            dates = extractors.extract_dates(line)
            if not dates:
                continue
            start, end = dates[0]
            entries.append(
                RawExperienceEntry(
                    company=line,
                    title=line,
                    start_date=start,
                    end_date=end,
                    description=line,
                )
            )
        return entries
