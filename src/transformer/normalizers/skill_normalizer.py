"""Skill casing, alias resolution, and deduplication.

The alias map is supplied by the caller (loaded from
``transformer.config.skill_aliases`` in production) rather than hardcoded
here, so curators can extend coverage without touching code.
"""

from transformer.normalizers.string_normalizer import clean


def normalize_skill(raw: str, alias_map: dict[str, str] | None = None) -> str:
    """Normalize a single skill string.

    Args:
        raw: Raw skill string.
        alias_map: Mapping of lower-cased alias -> canonical display form
            (e.g. ``{"js": "JavaScript"}``). If ``raw`` (lower-cased, after
            cleaning) matches a key, the canonical form is returned;
            otherwise the cleaned original is returned unchanged.

    Returns:
        The canonical skill string.
    """
    cleaned = clean(raw)
    if alias_map is None:
        return cleaned
    canonical = alias_map.get(cleaned.lower())
    return canonical if canonical is not None else cleaned


def normalize_skills(
    raw_skills: list[str], alias_map: dict[str, str] | None = None
) -> list[str]:
    """Normalize and deduplicate a list of skills, case-insensitively.

    Args:
        raw_skills: Raw skill strings.
        alias_map: Optional alias map; see ``normalize_skill``.

    Returns:
        Deduplicated list of canonical skill strings, preserving the order
        of first occurrence.
    """
    seen: set[str] = set()
    result: list[str] = []
    for raw in raw_skills:
        normalized = normalize_skill(raw, alias_map)
        if not normalized:
            continue
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            result.append(normalized)
    return result
