"""Unit tests for transformer.models.contact."""

from pydantic import ValidationError
import pytest

from transformer.models.contact import ContactInfo


@pytest.mark.unit
class TestContactInfo:
    """Tests for ContactInfo."""

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_all_fields(self) -> None:
        c = ContactInfo(
            email="alice@example.com",
            phone="+1-555-0100",
            location="San Francisco, CA",
            linkedin_url="https://linkedin.com/in/alice",
            github_url="https://github.com/alice",
        )
        assert c.email == "alice@example.com"
        assert c.phone == "+1-555-0100"
        assert c.location == "San Francisco, CA"

    def test_all_none(self) -> None:
        c = ContactInfo()
        assert c.email is None
        assert c.phone is None
        assert c.location is None
        assert c.linkedin_url is None
        assert c.github_url is None

    def test_email_only(self) -> None:
        c = ContactInfo(email="bob@example.org")
        assert c.email == "bob@example.org"

    def test_phone_stripped(self) -> None:
        c = ContactInfo(phone="  +44 20 7946 0958  ")
        assert c.phone == "+44 20 7946 0958"

    def test_location_stripped(self) -> None:
        c = ContactInfo(location="  London, UK  ")
        assert c.location == "London, UK"

    def test_url_serialised_as_string(self) -> None:
        c = ContactInfo(linkedin_url="https://linkedin.com/in/alice")
        serialised = c.model_dump()
        assert isinstance(serialised["linkedin_url"], str)

    def test_unicode_location(self) -> None:
        c = ContactInfo(location="São Paulo, Brasil")
        assert c.location == "São Paulo, Brasil"

    # ------------------------------------------------------------------
    # Negative path
    # ------------------------------------------------------------------

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactInfo(email="not-an-email")

    def test_invalid_linkedin_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactInfo(linkedin_url="not-a-url")

    def test_invalid_github_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactInfo(github_url="ftp://github.com/alice")

    def test_blank_phone_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactInfo(phone="   ")

    def test_blank_location_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactInfo(location="")

    def test_empty_phone_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactInfo(phone="")

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ContactInfo(unexpected="field")

    def test_frozen(self) -> None:
        c = ContactInfo(email="x@example.com")
        with pytest.raises(ValidationError):
            c.email = "y@example.com"  # type: ignore[misc]
