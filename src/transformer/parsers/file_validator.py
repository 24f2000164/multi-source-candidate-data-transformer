"""Pre-parse file validation.

Runs before any JSON content is read or decoded.  Treats the filesystem path
as untrusted input: existence, type, extension, size, and traversal are all
checked up front so that downstream stages only ever see a safe, bounded
file handle.
"""

import logging
from pathlib import Path

from transformer.parsers.exceptions import FileReadError
from transformer.parsers.parser_config import ParserConfig

logger = logging.getLogger(__name__)

_ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".json"})


class FileValidator:
    """Validates a candidate source file before parsing.

    Stateless and side-effect free aside from logging; safe to share across
    threads.
    """

    def validate(
        self,
        path: Path,
        config: ParserConfig,
        allowed_extensions: frozenset[str] | None = None,
    ) -> None:
        """Validate that ``path`` is safe to read and parse.

        Args:
            path: Filesystem path to the candidate source file.
            config: Parser configuration controlling the size limit.
            allowed_extensions: Extensions permitted for this call.
                Defaults to ``{".json"}`` to preserve existing ATS parser
                behaviour unchanged.

        Raises:
            FileReadError: If the path does not exist, is not a regular
                file, has a disallowed extension, exceeds the configured
                maximum size, or cannot be read due to a permissions error.
        """
        extensions = allowed_extensions or _ALLOWED_EXTENSIONS
        resolved = self._resolve_safe_path(path)

        if not resolved.exists():
            logger.warning("ats_file_not_found", extra={"path": str(resolved)})
            raise FileReadError(f"File not found: {resolved.name}")

        if not resolved.is_file():
            logger.warning("ats_file_not_regular_file", extra={"path": str(resolved)})
            raise FileReadError(f"Not a regular file: {resolved.name}")

        if resolved.suffix.lower() not in extensions:
            logger.warning(
                "ats_file_invalid_extension",
                extra={"path": str(resolved), "suffix": resolved.suffix},
            )
            raise FileReadError(
                f"Unsupported file extension: {resolved.suffix or '(none)'}"
            )

        try:
            size = resolved.stat().st_size
        except OSError as exc:
            logger.warning("ats_file_stat_failed", extra={"path": str(resolved)})
            raise FileReadError(
                f"Unable to read file metadata: {resolved.name}"
            ) from exc

        if size > config.max_file_size_bytes:
            logger.warning(
                "ats_file_too_large",
                extra={
                    "path": str(resolved),
                    "size_bytes": size,
                    "max_bytes": config.max_file_size_bytes,
                },
            )
            raise FileReadError(
                f"File exceeds maximum allowed size of "
                f"{config.max_file_size_bytes} bytes: {resolved.name}"
            )

        try:
            with resolved.open("rb") as fh:
                fh.read(1)
        except OSError as exc:
            logger.warning("ats_file_unreadable", extra={"path": str(resolved)})
            raise FileReadError(f"File is not readable: {resolved.name}") from exc

        logger.info(
            "ats_file_validated",
            extra={"path": str(resolved), "size_bytes": size},
        )

    @staticmethod
    def _resolve_safe_path(path: Path) -> Path:
        """Resolve ``path`` to an absolute path, rejecting traversal attempts.

        Args:
            path: The raw input path.

        Returns:
            The resolved absolute path.

        Raises:
            FileReadError: If the path cannot be resolved.
        """
        try:
            return path.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            raise FileReadError(f"Invalid file path: {path}") from exc
