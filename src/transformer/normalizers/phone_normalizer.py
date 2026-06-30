"""Phone number normalization backed by the ``phonenumbers`` library.

Phone normalization without a known region is inherently ambiguous (a raw
string like ``"020 7946 0958"`` is valid in several countries). This module
resolves the ambiguity explicitly:

* If the raw value already contains a ``+`` country-calling-code prefix, it
  is parsed without a default region.
* Otherwise a caller-supplied ``default_region`` (ISO 3166-1 alpha-2, e.g.
  ``"US"``) is used. If parsing still fails, the original trimmed string is
  returned unchanged rather than raising -- normalization is best-effort and
  must never discard data the merge engine could otherwise use.
"""

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

from transformer.normalizers.string_normalizer import trim

_DEFAULT_REGION = "US"


def normalize_phone(raw: str, default_region: str = _DEFAULT_REGION) -> str:
    """Normalize a raw phone string to E.164 form when possible.

    Args:
        raw: Raw phone number string as extracted from a source document.
        default_region: ISO 3166-1 alpha-2 region code used when ``raw``
            does not contain an explicit ``+`` country code prefix.

    Returns:
        The E.164-formatted number (e.g. ``"+14155552671"``) when ``raw``
        parses to a valid number. If parsing fails or the number is not
        valid for the resolved region, the trimmed original string is
        returned unchanged so no information is lost.
    """
    cleaned = trim(raw)
    if not cleaned:
        return cleaned

    region = None if cleaned.startswith("+") else default_region
    try:
        parsed = phonenumbers.parse(cleaned, region)
    except NumberParseException:
        return cleaned

    if not phonenumbers.is_valid_number(parsed):
        return cleaned

    return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
