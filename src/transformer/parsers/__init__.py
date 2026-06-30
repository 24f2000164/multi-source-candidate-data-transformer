"""Public API for the transformer.parsers package.

Example::

    from transformer.parsers import ATSParser, ParserConfig

    parser = ATSParser()
    candidate = parser.parse(Path("samples/inputs/ats_sample.json"))
"""

from transformer.parsers.ats_mapper import ATSMapper
from transformer.parsers.ats_parser import ATSParser
from transformer.parsers.base_parser import BaseParser
from transformer.parsers.exceptions import (
    FileReadError,
    InvalidJSONError,
    MappingError,
    ParserError,
    SchemaValidationError,
)
from transformer.parsers.file_validator import FileValidator
from transformer.parsers.parser_config import ParserConfig
from transformer.parsers.schema_validator import SchemaValidator

__all__ = [
    "ATSMapper",
    "ATSParser",
    "BaseParser",
    "FileReadError",
    "FileValidator",
    "InvalidJSONError",
    "MappingError",
    "ParserConfig",
    "ParserError",
    "SchemaValidationError",
    "SchemaValidator",
]
