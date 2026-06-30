"""Exception hierarchy for the transformer.projection package."""


class ProjectionError(Exception):
    """Base class for all projection-layer errors.

    Attributes:
        message: A safe, human-readable description of the failure.
    """

    def __init__(self, message: str) -> None:
        """Initialise the error with a safe message.

        Args:
            message: A safe, human-readable description of the failure.
        """
        super().__init__(message)
        self.message = message


class UnknownProjectionTypeError(ProjectionError):
    """Raised when a requested projection type is not registered."""
