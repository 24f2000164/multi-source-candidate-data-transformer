"""Hash-based, O(n) duplicate detection for experiences and education.

Normalisation happens before hashing: lowercase, strip, collapse internal
whitespace. Without this, "Google" / "GOOGLE" / "Google " would hash to
distinct keys and silently evade duplicate detection.
"""

import re

from transformer.models import Candidate
from transformer.validation.rule import Severity, ValidationIssue

_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_key_part(value: object) -> str:
    """Normalise a single key component for duplicate-key hashing.

    Args:
        value: The raw value (string, date, or ``None``).

    Returns:
        Lowercased, trimmed, whitespace-collapsed string representation.
    """
    text = "" if value is None else str(value)
    text = text.strip().lower()
    return _WHITESPACE_RE.sub(" ", text)


class DuplicateExperienceRule:
    """Flags work experience entries that look like duplicates.

    Key: ``company|title|start_date``, normalised before hashing.
    Complexity: O(n) in the number of experience entries.
    """

    name = "duplicate_experience"
    severity = Severity.WARNING

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Scan ``candidate.experiences`` for normalised-key collisions.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue per experience entry whose key collides with an
            earlier entry.
        """
        issues: list[ValidationIssue] = []
        seen: set[str] = set()
        for i, exp in enumerate(candidate.experiences):
            key = "|".join(
                _normalize_key_part(v) for v in (exp.company, exp.title, exp.start_date)
            )
            if key in seen:
                issues.append(
                    ValidationIssue(
                        rule_name=self.name,
                        severity=self.severity,
                        field=f"experiences[{i}]",
                        message=(
                            f"possible duplicate experience: "
                            f"{exp.company!r} / {exp.title!r}"
                        ),
                        suggestion="confirm this is not the same role reported twice",
                    )
                )
            else:
                seen.add(key)
        return issues


class DuplicateEducationRule:
    """Flags education entries that look like duplicates.

    Key: ``institution|degree``, normalised before hashing.
    Complexity: O(n) in the number of education entries.
    """

    name = "duplicate_education"
    severity = Severity.WARNING

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Scan ``candidate.education`` for normalised-key collisions.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue per education entry whose key collides with an
            earlier entry.
        """
        issues: list[ValidationIssue] = []
        seen: set[str] = set()
        for i, edu in enumerate(candidate.education):
            key = "|".join(
                _normalize_key_part(v) for v in (edu.institution, edu.degree)
            )
            if key in seen:
                issues.append(
                    ValidationIssue(
                        rule_name=self.name,
                        severity=self.severity,
                        field=f"education[{i}]",
                        message=(
                            f"possible duplicate education: "
                            f"{edu.institution!r} / {edu.degree!r}"
                        ),
                        suggestion="confirm this is not the same credential twice",
                    )
                )
            else:
                seen.add(key)
        return issues
