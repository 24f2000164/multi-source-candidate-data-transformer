"""Cross-field validation rules.

Run after duplicate detection in the default pipeline ordering (Schema ->
Business -> Duplicate -> Cross-Field): cross-field consistency checks are
easier to reason about, and easier to debug, once duplicates are already
known and flagged separately.
"""

from transformer.models import Candidate
from transformer.validation.rule import Severity, ValidationIssue


class DateOrderRule:
    """Confirms ``end_date >= start_date`` for every experience/education entry.

    Defense in depth: both ``WorkExperience`` and ``Education`` already
    enforce this via a pydantic ``model_validator``. ``Education`` allows
    ``start_date`` to be ``None`` (ongoing/unspecified), which is exempt.
    """

    name = "date_order"
    severity = Severity.ERROR

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check date ordering across experiences and education entries.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue per entry where ``end_date`` precedes ``start_date``.
        """
        issues: list[ValidationIssue] = []
        for i, exp in enumerate(candidate.experiences):
            if exp.end_date is not None and exp.end_date < exp.start_date:
                issues.append(
                    ValidationIssue(
                        rule_name=self.name,
                        severity=self.severity,
                        field=f"experiences[{i}].end_date",
                        message="end_date is before start_date",
                    )
                )
        for i, edu in enumerate(candidate.education):
            if (
                edu.start_date is not None
                and edu.end_date is not None
                and edu.end_date < edu.start_date
            ):
                issues.append(
                    ValidationIssue(
                        rule_name=self.name,
                        severity=self.severity,
                        field=f"education[{i}].end_date",
                        message="end_date is before start_date",
                    )
                )
        return issues


class ConfidenceFieldConsistencyRule:
    """Confirms ``confidence.fields`` keys correspond to real model fields.

    A confidence field key like ``"contact.bogus_field"`` indicates the
    confidence engine and the model have drifted out of sync, which would
    otherwise fail silently.
    """

    name = "confidence_field_consistency"
    severity = Severity.WARNING

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check every confidence field key resolves to a real attribute.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue per confidence field key that does not resolve.
        """
        if candidate.confidence is None:
            return []

        issues: list[ValidationIssue] = []
        for field_name in candidate.confidence.fields:
            if not self._resolves(candidate, field_name):
                issues.append(
                    ValidationIssue(
                        rule_name=self.name,
                        severity=self.severity,
                        field=field_name,
                        message=(
                            f"confidence field '{field_name}' does not "
                            "correspond to a known candidate field"
                        ),
                    )
                )
        return issues

    def _resolves(self, candidate: Candidate, field_name: str) -> bool:
        """Check whether a dotted field name resolves on the candidate model.

        Args:
            candidate: The candidate record.
            field_name: Dotted field name, e.g. ``"contact.email"``.

        Returns:
            ``True`` if every segment of ``field_name`` exists as an
            attribute (even if its current value is ``None``).
        """
        obj: object = candidate
        for part in field_name.split("."):
            model_fields = getattr(type(obj), "model_fields", None)
            if model_fields is None or part not in model_fields:
                return False
            obj = getattr(obj, part, None)
            if obj is None:
                return True
        return True
