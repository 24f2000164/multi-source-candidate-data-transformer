"""Structured result returned by the application service."""

from dataclasses import dataclass
from typing import Any

from transformer.models import Candidate


@dataclass(frozen=True)
class ApplicationResult:
    """Application-layer result independent of CLI rendering concerns."""

    candidate: Candidate | None
    projection: dict[str, Any] | None
    reports: dict[str, object]
    warnings: list[str]
    success: bool
    exit_code: int
