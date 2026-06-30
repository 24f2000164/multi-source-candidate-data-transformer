"""``ProjectionRegistry``: constructor-injected, immutable set of strategies."""

from transformer.projection.exceptions import UnknownProjectionTypeError
from transformer.projection.projection_strategy import ProjectionStrategy


class ProjectionRegistry:
    """Holds the projection strategies a ``ProjectionEngine`` can use.

    Immutable after construction: all strategies are supplied up front via
    constructor injection. There is no public ``register()`` method, so a
    registry's contents can never be mutated at runtime -- adding a new
    projection type means adding it to the constructor mapping (typically in
    pipeline/CLI wiring), never touching ``ProjectionEngine`` itself.
    """

    def __init__(self, strategies: dict[str, ProjectionStrategy]) -> None:
        """Initialise the registry with its strategy instances.

        Args:
            strategies: Mapping of projection type name to the strategy
                instance that handles it.
        """
        self._strategies: dict[str, ProjectionStrategy] = dict(strategies)

    def get(self, projection_type: str) -> ProjectionStrategy:
        """Look up the strategy registered for a projection type.

        Args:
            projection_type: Name of the requested projection type.

        Returns:
            The registered ``ProjectionStrategy``.

        Raises:
            UnknownProjectionTypeError: If no strategy is registered under
                ``projection_type``.
        """
        try:
            return self._strategies[projection_type]
        except KeyError:
            raise UnknownProjectionTypeError(
                f"unknown projection type: {projection_type!r}"
            ) from None
