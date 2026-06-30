"""Exception hierarchy for the transformer.parsers package.

All exceptions carry a safe, user-facing ``message`` only.  Internal
exception chaining (``raise X from e``) preserves the original traceback for
logs, but the message surfaced to callers never includes raw stack traces or
internal implementation detail.
"""


class ParserError(Exception):
    """Base class for all parser-related errors.

    Attributes:
        message: A safe, human-readable description of the failure.
    """

    def __init__(self, message: str) -> None:
        """Initialise the error with a safe message.

        Args:
            message: A safe, human-readable description of the failure.
        """
        super().__init__(message)
        self.message = message


class FileReadError(ParserError):
    """Raised when a source file cannot be safely read.

    Covers: missing file, not a regular file, unreadable, path traversal,
    disallowed extension, and oversized file.
    """


class InvalidJSONError(ParserError):
    """Raised when the source content is not valid JSON.

    Covers: JSON syntax errors and undecodable byte content (e.g. malformed
    UTF-8).
    """


class SchemaValidationError(ParserError):
    """Raised when parsed JSON does not satisfy the required ATS schema.

    Covers: missing required fields, wrong top-level types, and null values
    for required fields.
    """


class MappingError(ParserError):
    """Raised when validated JSON cannot be mapped to the Canonical Model.

    Covers: Pydantic validation failures during canonical model construction,
    and invalid required nested objects (e.g. an experience entry missing a
    required field).
    """
