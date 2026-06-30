"""Exception hierarchy for the transformer.validation package."""


class ValidationEngineError(Exception):
    """Base class for all validation-engine related errors.

    Note: deliberately not named ``ValidationError`` to avoid colliding with
    ``pydantic.ValidationError``, which several call sites also handle.

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


class DuplicateRuleNameError(ValidationEngineError):
    """Raised when two ``ValidationRule`` instances share a name in a registry."""
