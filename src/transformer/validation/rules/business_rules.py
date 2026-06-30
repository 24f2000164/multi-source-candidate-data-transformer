"""Business-level validation rules: format and domain-validity checks."""

import re

import phonenumbers
from phonenumbers import NumberParseException

from transformer.models import Candidate
from transformer.validation.rule import Severity, ValidationIssue

# external_id: non-blank, reasonable length, conservative charset.
_EXTERNAL_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
_EXTERNAL_ID_MAX_LENGTH = 128


class EmailFormatRule:
    """Re-validates email format (defense in depth over ``EmailStr``)."""

    name = "email_format"
    severity = Severity.ERROR

    _PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check ``contact.email`` against a conservative format pattern.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue if the email is present but malformed, else none.
        """
        if candidate.contact is None or candidate.contact.email is None:
            return []
        email = str(candidate.contact.email)
        if not self._PATTERN.match(email):
            return [
                ValidationIssue(
                    rule_name=self.name,
                    severity=self.severity,
                    field="contact.email",
                    message=f"email does not match expected format: {email!r}",
                    suggestion="provide a valid RFC-5322 email address",
                    candidate_value=repr(email),
                )
            ]
        return []


class PhoneFormatRule:
    """Validates ``contact.phone`` using the ``phonenumbers`` library.

    ``ContactInfo.phone`` is a raw string with no model-level format
    validation (normalisation happens elsewhere), so this is the first real
    validity check on it.
    """

    name = "phone_format"
    severity = Severity.WARNING

    def __init__(self, *, default_region: str = "US") -> None:
        """Initialise with the default region used when parsing.

        Args:
            default_region: ISO 3166-1 alpha-2 region used when the raw
                phone string has no explicit ``+`` country code.
        """
        self._default_region = default_region

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check ``contact.phone`` for a parseable, valid phone number.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue if the phone is present but invalid, else none.
        """
        if candidate.contact is None or not candidate.contact.phone:
            return []
        raw = candidate.contact.phone
        try:
            parsed = phonenumbers.parse(raw, self._default_region)
            valid = phonenumbers.is_valid_number(parsed)
        except NumberParseException:
            valid = False
        if not valid:
            return [
                ValidationIssue(
                    rule_name=self.name,
                    severity=self.severity,
                    field="contact.phone",
                    message=f"phone number is not valid: {raw!r}",
                    suggestion="provide a number including country code",
                    candidate_value=repr(raw),
                )
            ]
        return []


class UrlFormatRule:
    """Re-checks LinkedIn/GitHub URLs (defense in depth over ``AnyHttpUrl``)."""

    name = "url_format"
    severity = Severity.WARNING

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check that ``linkedin_url``/``github_url`` use http(s) schemes.

        Args:
            candidate: The candidate record to validate.

        Returns:
            One issue per malformed URL field.
        """
        if candidate.contact is None:
            return []
        issues: list[ValidationIssue] = []
        for field in ("linkedin_url", "github_url"):
            url = getattr(candidate.contact, field)
            if url is None:
                continue
            if str(url.scheme) not in ("http", "https"):
                issues.append(
                    ValidationIssue(
                        rule_name=self.name,
                        severity=self.severity,
                        field=f"contact.{field}",
                        message=f"'{field}' must use http or https",
                        candidate_value=repr(str(url)),
                    )
                )
        return issues


class ExternalIdRule:
    """Validates ``external_id``: non-blank, conservative pattern, bounded length."""

    name = "external_id_format"
    severity = Severity.ERROR

    def check(self, candidate: Candidate) -> list[ValidationIssue]:
        """Check ``external_id`` for blankness, pattern, and length overflow.

        Args:
            candidate: The candidate record to validate.

        Returns:
            Zero or more issues for an invalid ``external_id``.
        """
        external_id = candidate.external_id
        if external_id is None:
            return []

        issues: list[ValidationIssue] = []
        if not external_id.strip():
            issues.append(
                ValidationIssue(
                    rule_name=self.name,
                    severity=self.severity,
                    field="external_id",
                    message="external_id is blank",
                )
            )
            return issues

        if len(external_id) > _EXTERNAL_ID_MAX_LENGTH:
            issues.append(
                ValidationIssue(
                    rule_name=self.name,
                    severity=self.severity,
                    field="external_id",
                    message=(
                        f"external_id exceeds max length "
                        f"({len(external_id)} > {_EXTERNAL_ID_MAX_LENGTH})"
                    ),
                )
            )
        elif not _EXTERNAL_ID_PATTERN.match(external_id):
            issues.append(
                ValidationIssue(
                    rule_name=self.name,
                    severity=self.severity,
                    field="external_id",
                    message=f"external_id has unexpected characters: {external_id!r}",
                    suggestion="use only letters, digits, '.', '_', ':', '-'",
                    candidate_value=repr(external_id),
                )
            )
        return issues
