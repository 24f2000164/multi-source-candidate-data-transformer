"""``ProjectionStrategy``: the contract every projection type implements."""

from abc import ABC, abstractmethod
from typing import Any

from transformer.models import Candidate


class ProjectionStrategy(ABC):
    """Projects a ``Candidate`` into a JSON-safe ``dict``.

    Implementations must be stateless, read-only, and must never mutate the
    ``Candidate`` they are given (it is a frozen Pydantic model, so this is
    enforced structurally as well as by convention).
    """

    @abstractmethod
    def project(self, candidate: Candidate) -> dict[str, Any]:
        """Project a candidate into its output dict shape.

        Args:
            candidate: The canonical candidate record to project.

        Returns:
            A JSON-safe ``dict`` representing the projected output.
        """
        raise NotImplementedError
