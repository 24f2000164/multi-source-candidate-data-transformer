"""Private shared validator helpers for the transformer.models package.

Not part of the public API. Import only within transformer.models submodules.
"""

from typing import Any


def strip_non_empty(v: Any) -> Any:
    """Strip whitespace from a string and reject blank results.

    Args:
        v: The raw field value.

    Returns:
        The stripped string, or the original value if it is not a string.

    Raises:
        ValueError: If the string is empty or whitespace-only after stripping.
    """
    if isinstance(v, str):
        stripped = v.strip()
        if not stripped:
            raise ValueError("value must not be blank")
        return stripped
    return v


def deduplicate_strings(v: Any) -> Any:
    """Remove duplicate strings from a list while preserving insertion order.

    Blank strings and whitespace-only strings are silently dropped.

    Args:
        v: The raw list field value.

    Returns:
        A deduplicated list.  Non-string items are preserved as-is.
    """
    if not isinstance(v, list):
        return v
    seen: set[str] = set()
    result: list[Any] = []
    for item in v:
        if isinstance(item, str):
            normalized = item.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        else:
            result.append(item)
    return result
