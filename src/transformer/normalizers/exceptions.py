"""Exception hierarchy for the transformer.normalizers package.

Mirrors the pattern established in ``transformer.parsers.exceptions``: all
exceptions carry a safe, human-readable ``message`` only.
"""


class NormalizationError(Exception):
    """Base class for all normalization-related errors.

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
