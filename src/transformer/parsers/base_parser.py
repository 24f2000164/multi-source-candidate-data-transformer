"""Abstract base class for all source-to-canonical parsers.

Implements the Strategy pattern (TDR-13): each concrete parser (ATS JSON,
Resume PDF, ...) implements the same interface so the pipeline orchestrator
can depend only on this abstraction, not on any concrete parser.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from transformer.models import Candidate


class BaseParser(ABC):
    """Interface for converting a source file into a Canonical Candidate."""

    @abstractmethod
    def parse(self, source: Path) -> Candidate:
        """Parse ``source`` into a fully validated Candidate model.

        Args:
            source: Filesystem path to the source file.

        Returns:
            A validated ``Candidate`` instance.

        Raises:
            transformer.parsers.exceptions.ParserError: If parsing fails for
                any reason (see concrete parser documentation for the exact
                exception subtype raised).
        """
        raise NotImplementedError
