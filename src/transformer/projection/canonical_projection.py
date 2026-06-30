"""``CanonicalProjection``: returns the full ``Candidate`` as JSON-safe dict."""

from typing import Any

from transformer.models import Candidate
from transformer.projection.projection_strategy import ProjectionStrategy


class CanonicalProjection(ProjectionStrategy):
    """Projects a candidate into its full canonical JSON representation.

    Delegates entirely to Pydantic's ``model_dump(mode="json")``, which
    already handles ``UUID``, ``datetime``, ``date``, and ``Enum`` values
    correctly, so no custom serialization logic is required here.
    """

    def project(self, candidate: Candidate) -> dict[str, Any]:
        """Return the full candidate as a JSON-safe dict.

        Args:
            candidate: The canonical candidate record to project.

        Returns:
            The complete candidate, JSON-safe, with all fields present.
        """
        return candidate.model_dump(mode="json")
