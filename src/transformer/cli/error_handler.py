"""Centralized translation of internal exceptions into CLI failures."""

import traceback
from typing import NoReturn

from pydantic import ValidationError
import typer

from transformer.config.exceptions import ConfigError
from transformer.merge.exceptions import MergeError
from transformer.normalizers.exceptions import NormalizationError
from transformer.parsers.exceptions import ParserError, SchemaValidationError
from transformer.projection.exceptions import (
    ProjectionError,
    UnknownProjectionTypeError,
)
from transformer.validation.exceptions import ValidationEngineError


def handle_cli_error(error: Exception, *, debug: bool) -> NoReturn:
    """Print one safe error message, optionally with a debug traceback."""
    if debug:
        traceback.print_exception(type(error), error, error.__traceback__)
    else:
        typer.echo(_user_message(error), err=True)
    raise typer.Exit(code=1)


def _user_message(error: Exception) -> str:
    if isinstance(error, FileNotFoundError):
        path = error.filename or str(error)
        return f"File not found: {path}"
    if isinstance(error, SchemaValidationError):
        return f"Input does not match expected schema: {error}"
    if isinstance(error, ParserError):
        return f"Could not parse file: {error}"
    if isinstance(error, MergeError):
        return f"Merge conflict: {error}"
    if isinstance(error, UnknownProjectionTypeError):
        return f"Unknown projection format: {error}"
    if isinstance(error, ProjectionError):
        return f"Projection failed: {error}"
    if isinstance(error, ConfigError):
        return f"Configuration error: {error}"
    if isinstance(error, NormalizationError):
        return f"Normalization failed: {error}"
    if isinstance(error, ValidationEngineError):
        return f"Candidate data failed validation: {error}"
    if isinstance(error, ValidationError):
        return f"Candidate data is invalid: {error.error_count()} error(s)"
    if isinstance(error, OSError):
        return f"File operation failed: {error}"
    return "Unexpected error. Run with --debug for details."
