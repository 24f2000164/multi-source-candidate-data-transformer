"""Configuration for parser components.

Keeps tunable values (max file size, encoding, strict mode) out of
hardcoded constants so they can be overridden per environment or per call
without touching parser logic.  This is intentionally a small, local config
object for the parsers package -- the broader pipeline-wide configuration
loading system is out of scope for Sprint 02 (see Sprint 08).
"""

from dataclasses import dataclass

_DEFAULT_MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
_DEFAULT_ENCODING: str = "utf-8-sig"  # tolerates a leading UTF-8 BOM


@dataclass(frozen=True)
class ParserConfig:
    """Tunable configuration for ATS parsing.

    Attributes:
        max_file_size_bytes: Maximum allowed size of a source file, in
            bytes. Files larger than this are rejected before JSON parsing
            to guard against resource exhaustion.
        encoding: Text encoding used to read source files. Defaults to
            ``"utf-8-sig"`` so a leading byte-order mark is tolerated
            transparently.
        strict_mode: When ``True`` (default), unknown fields are logged as
            warnings but never cause a parse failure. Reserved for future
            stricter behaviour without changing the parser's public API.
    """

    max_file_size_bytes: int = _DEFAULT_MAX_FILE_SIZE_BYTES
    encoding: str = _DEFAULT_ENCODING
    strict_mode: bool = True
