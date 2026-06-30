"""Unit tests for transformer.validation.rules.business_rules."""

from transformer.models import ContactInfo
from transformer.validation.rules.business_rules import (
    ExternalIdRule,
    PhoneFormatRule,
    UrlFormatRule,
)

from tests.unit.validation._builders import make_candidate


def test_phone_format_passes_for_valid_number() -> None:
    candidate = make_candidate(contact=ContactInfo(phone="+14155552671"))
    assert PhoneFormatRule().check(candidate) == []


def test_phone_format_flags_invalid_number() -> None:
    candidate = make_candidate(contact=ContactInfo(phone="123"))
    issues = PhoneFormatRule().check(candidate)
    assert len(issues) == 1
    assert issues[0].field == "contact.phone"


def test_phone_format_passes_when_absent() -> None:
    candidate = make_candidate(contact=None)
    assert PhoneFormatRule().check(candidate) == []


def test_url_format_passes_for_https_urls() -> None:
    candidate = make_candidate(
        contact=ContactInfo(linkedin_url="https://linkedin.com/in/jane")
    )
    assert UrlFormatRule().check(candidate) == []


def test_external_id_rule_passes_for_valid_id() -> None:
    candidate = make_candidate(external_id="ATS-12345")
    assert ExternalIdRule().check(candidate) == []


def test_external_id_rule_flags_bad_characters() -> None:
    candidate = make_candidate(external_id="bad id!!")
    issues = ExternalIdRule().check(candidate)
    assert len(issues) == 1
    assert issues[0].field == "external_id"


def test_external_id_rule_flags_overflow_length() -> None:
    candidate = make_candidate(external_id="x" * 200)
    issues = ExternalIdRule().check(candidate)
    assert len(issues) == 1
    assert "max length" in issues[0].message


def test_external_id_rule_passes_when_absent() -> None:
    candidate = make_candidate(external_id=None)
    assert ExternalIdRule().check(candidate) == []
