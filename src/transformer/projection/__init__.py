"""Public API for the transformer.projection package.

Example::

    from transformer.projection import (
        AssignmentProjection,
        CanonicalProjection,
        ProjectionEngine,
        ProjectionRegistry,
        ProjectionReport,
    )

    registry = ProjectionRegistry(
        {
            "canonical": CanonicalProjection(),
            "assignment": AssignmentProjection(),
        }
    )
    engine = ProjectionEngine(registry)
    output, report = engine.project(candidate, "canonical")
"""

from transformer.projection.assignment_projection import AssignmentProjection
from transformer.projection.canonical_projection import CanonicalProjection
from transformer.projection.exceptions import (
    ProjectionError,
    UnknownProjectionTypeError,
)
from transformer.projection.projection_engine import ProjectionEngine
from transformer.projection.projection_registry import ProjectionRegistry
from transformer.projection.projection_report import ProjectionReport
from transformer.projection.projection_strategy import ProjectionStrategy

__all__ = [
    "AssignmentProjection",
    "CanonicalProjection",
    "ProjectionEngine",
    "ProjectionError",
    "ProjectionRegistry",
    "ProjectionReport",
    "ProjectionStrategy",
    "UnknownProjectionTypeError",
]
