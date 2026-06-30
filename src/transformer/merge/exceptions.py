"""Exception hierarchy for the transformer.merge package."""


class MergeError(Exception):
    """Base class for all merge-related errors.

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
