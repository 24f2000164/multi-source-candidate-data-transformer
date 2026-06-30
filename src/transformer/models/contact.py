"""Contact information model for a candidate."""

from typing import Annotated, Any

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PlainSerializer,
    field_validator,
)

# AnyHttpUrl serialised as a plain string for clean JSON output.
HttpUrlStr = Annotated[AnyHttpUrl, PlainSerializer(str, return_type=str)]


class ContactInfo(BaseModel):
    """Contact details for a candidate.

    All fields are optional because either the ATS record or the resume may
    be the sole data provider.

    Attributes:
        email: Validated RFC-5322 email address.
        phone: Raw phone string (normalised in Sprint 4).
        location: Free-text location (city, country, etc.).
        linkedin_url: LinkedIn profile URL.
        github_url: GitHub profile URL.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    email: EmailStr | None = Field(None, description="Validated email address.")
    phone: str | None = Field(None, description="Raw phone number string.")
    location: str | None = Field(None, description="Free-text location.")
    linkedin_url: HttpUrlStr | None = Field(None, description="LinkedIn profile URL.")
    github_url: HttpUrlStr | None = Field(None, description="GitHub profile URL.")

    @field_validator("phone", "location", mode="before")
    @classmethod
    def _strip_and_reject_blank(cls, v: Any) -> Any:
        """Strip whitespace; reject the field if it resolves to blank.

        Args:
            v: Raw field value.

        Returns:
            The stripped string, or the original non-string value.

        Raises:
            ValueError: If a provided string is empty after stripping.
        """
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError("field must not be blank")
            return stripped
        return v
