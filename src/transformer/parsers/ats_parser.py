"""ATS JSON parser: the first input adapter of the transformation pipeline.

Converts a structured ATS JSON file into the Canonical Candidate Model.
Deterministic and stateless: given the same file and configuration, this
parser always produces the same result (or the same exception). Safe to use
concurrently across threads -- it holds no mutable instance state.
"""

import json
import logging
from pathlib import Path
from typing import Any, cast

from transformer.models import Candidate
from transformer.parsers.ats_mapper import ATSMapper
from transformer.parsers.base_parser import BaseParser
from transformer.parsers.exceptions import FileReadError, InvalidJSONError
from transformer.parsers.file_validator import FileValidator
from transformer.parsers.parser_config import ParserConfig
from transformer.parsers.schema_validator import SchemaValidator

logger = logging.getLogger(__name__)


class ATSParser(BaseParser):
    """Parses ATS JSON files into validated Candidate models.

    Dependencies are injected via the constructor (TDR-19) so the parser can
    be unit tested with fakes/mocks and so file validation, schema
    validation, and mapping logic each remain independently swappable.
    """

    def __init__(
        self,
        file_validator: FileValidator | None = None,
        schema_validator: SchemaValidator | None = None,
        mapper: ATSMapper | None = None,
        config: ParserConfig | None = None,
    ) -> None:
        """Initialise the ATS parser with its collaborators.

        Args:
            file_validator: Validates the source file before parsing.
                Defaults to a new ``FileValidator``.
            schema_validator: Validates the raw JSON shape before mapping.
                Defaults to a new ``SchemaValidator``.
            mapper: Maps validated raw data to the canonical model.
                Defaults to a new ``ATSMapper``.
            config: Tunable parser configuration (file size limit, encoding,
                strict mode). Defaults to ``ParserConfig()``.
        """
        self._file_validator = file_validator or FileValidator()
        self._schema_validator = schema_validator or SchemaValidator()
        self._mapper = mapper or ATSMapper()
        self._config = config or ParserConfig()

    def parse(self, source: Path) -> Candidate:
        """Parse an ATS JSON file into a validated ``Candidate``.

        Args:
            source: Filesystem path to the ATS JSON file.

        Returns:
            A fully validated ``Candidate`` instance.

        Raises:
            FileReadError: If the file is missing, unreadable, has a
                disallowed extension, or exceeds the configured size limit.
            InvalidJSONError: If the file content is not valid JSON or
                cannot be decoded with the configured encoding.
            SchemaValidationError: If the JSON does not satisfy the required
                ATS schema (missing/blank/mistyped required fields).
            MappingError: If the validated data cannot be mapped to the
                canonical model (e.g. invalid nested experience entry).
        """
        logger.info("ats_parse_started", extra={"path": str(source)})

        self._file_validator.validate(source, self._config)

        data = self._load_json(source)

        validation_result = self._schema_validator.validate(data)
        if validation_result.unknown_fields:
            logger.warning(
                "ats_unknown_fields_ignored",
                extra={
                    "path": str(source),
                    "fields": validation_result.unknown_fields,
                },
            )
        logger.info("ats_schema_validated", extra={"path": str(source)})

        candidate = self._mapper.map_candidate(data)
        logger.info(
            "ats_parse_completed",
            extra={"path": str(source), "candidate_id": str(candidate.id)},
        )

        return candidate

    def _load_json(self, source: Path) -> dict[str, Any]:
        """Read and decode a JSON file using the configured encoding.

        Args:
            source: Filesystem path to the ATS JSON file.

        Returns:
            The decoded JSON content as a dictionary.

        Raises:
            FileReadError: If the file cannot be opened for reading.
            InvalidJSONError: If the content is not valid JSON or cannot be
                decoded with the configured encoding.
        """
        try:
            text = source.read_text(encoding=self._config.encoding)
        except UnicodeDecodeError as exc:
            logger.warning(
                "ats_invalid_encoding",
                extra={"path": str(source), "encoding": self._config.encoding},
            )
            raise InvalidJSONError(
                f"File is not valid {self._config.encoding} text: {source.name}"
            ) from exc
        except OSError as exc:
            logger.warning("ats_file_open_failed", extra={"path": str(source)})
            raise FileReadError(f"Unable to read file: {source.name}") from exc

        try:
            decoded: Any = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning(
                "ats_invalid_json_syntax",
                extra={"path": str(source), "error": str(exc)},
            )
            raise InvalidJSONError(
                f"File does not contain valid JSON: {source.name}"
            ) from exc

        logger.info("ats_json_loaded", extra={"path": str(source)})
        return cast("dict[str, Any]", decoded)
