"""Date coercion helpers backed by ``python-dateutil``.

Canonical model fields (``WorkExperience.start_date`` etc.) are already
typed as ``datetime.date`` by the time a ``Candidate`` exists -- Pydantic
performs that coercion during parsing. This module exists for two reasons:

1. Idempotency: re-running normalization on an already-normalized
   ``Candidate`` must be a safe no-op, so ``coerce_date`` accepts a
   ``date`` and returns it unchanged.
2. Defensive reuse: any future caller that still holds a raw string (e.g. a
   parser calling this ahead of model construction) gets the same
   best-effort coercion logic instead of duplicating it.

No future-date validation is performed here -- that rule already lives on
``WorkExperience._no_future_start`` and must not be duplicated.
"""

from datetime import date

from dateutil import parser as dateutil_parser

from transformer.normalizers.exceptions import NormalizationError


def coerce_date(value: date | str) -> date:
    """Coerce a date-like value to ``datetime.date``.

    Args:
        value: Either an already-parsed ``date`` (returned unchanged) or a
            raw date string in any format ``dateutil`` can recognise.

    Returns:
        The resulting ``date``.

    Raises:
        NormalizationError: If ``value`` is a string that cannot be parsed
            as a date.
    """
    if isinstance(value, date):
        return value
    try:
        return dateutil_parser.parse(value).date()
    except (ValueError, OverflowError) as exc:
        raise NormalizationError(f"could not parse date: {value!r}") from exc
