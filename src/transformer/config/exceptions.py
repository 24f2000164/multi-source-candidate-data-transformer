"""Exception hierarchy for the transformer.config package."""


class ConfigError(Exception):
    """Raised for any problem loading or validating a config file.

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
