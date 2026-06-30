"""``ProjectionEngine``: orchestrates a ``ProjectionRegistry`` against a ``Candidate``."""

from typing import Any

from transformer.models import Candidate
from transformer.projection.projection_registry import ProjectionRegistry
from transformer.projection.projection_report import ProjectionReport


class ProjectionEngine:
    """Validates a projection type, delegates to its strategy, and reports.

    Has no hardcoded strategy list -- it only knows about
    ``ProjectionRegistry``. Adding a new projection type never requires a
    change here (Open/Closed); it only requires adding the strategy to the
    registry's construction.
    """

    def __init__(self, registry: ProjectionRegistry) -> None:
        """Initialise the engine with its projection registry.

        Args:
            registry: The ``ProjectionRegistry`` used to resolve strategies.
        """
        self._registry = registry

    def project(
        self, candidate: Candidate, projection_type: str
    ) -> tuple[dict[str, Any], ProjectionReport]:
        """Project a candidate using the named projection type.

        Args:
            candidate: The canonical candidate record to project.
            projection_type: Name of the registered projection strategy to
                use (e.g. ``"canonical"`` or ``"assignment"``).

        Returns:
            A ``(output, report)`` tuple: the projected, JSON-safe dict and
            a ``ProjectionReport`` describing the run. ``output`` is
            returned separately from the report so callers are not forced
            to unpack potentially large payloads out of report metadata.

        Raises:
            UnknownProjectionTypeError: If ``projection_type`` is not
                registered.
        """
        strategy = self._registry.get(projection_type)
        output = strategy.project(candidate)

        return output, ProjectionReport(
            projection_type=projection_type,
            field_count=len(output),
            warnings=(),
        )
