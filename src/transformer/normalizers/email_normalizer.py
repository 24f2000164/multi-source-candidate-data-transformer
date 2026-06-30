"""Email normalization: trim + lowercase.

Validation (RFC-5322 syntax) is already enforced by ``ContactInfo.email``
(``pydantic.EmailStr``); this module only normalises casing/whitespace so
equal addresses compare equal during merge.
"""

from transformer.normalizers.string_normalizer import trim


def normalize_email(raw: str) -> str:
    """Lowercase and trim an email address.

    Args:
        raw: Raw email string.

    Returns:
        The trimmed, lowercased email address.
    """
    return trim(raw).lower()
