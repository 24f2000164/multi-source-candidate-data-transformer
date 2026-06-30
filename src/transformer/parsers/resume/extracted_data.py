"""Intermediate extraction contract between resume text mining and mapping.

``ExtractedResumeData`` is the typed boundary between everything that pulls
raw values out of PDF/DOCX text (``TextExtractor``, ``SectionDetector``,
``NameDetector``, ``extractors``) and everything that maps those values onto
the frozen Canonical Candidate Model (``ResumeMapper``). Deliberately loose
typing (raw strings for dates) -- date coercion happens in ``ResumeMapper``,
mirroring how ``ATSMapper`` handles raw ATS dicts.
"""

from pydantic import BaseModel, ConfigDict, Field


class RawExperienceEntry(BaseModel):
    """A single, not-yet-validated work experience entry extracted from text."""

    model_config = ConfigDict(extra="forbid")

    company: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class RawEducationEntry(BaseModel):
    """A single, not-yet-validated education entry extracted from text."""

    model_config = ConfigDict(extra="forbid")

    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: float | None = None


class RawCertificationEntry(BaseModel):
    """A single, not-yet-validated certification entry extracted from text."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    issuer: str | None = None
    issued_date: str | None = None
    expiry_date: str | None = None


class ExtractedResumeData(BaseModel):
    """Typed, intermediate result of resume text extraction.

    Constructible directly in tests without ever touching PDF/DOCX bytes,
    and consumed only by ``ResumeMapper`` -- never exposed outside the
    resume parser's own pipeline.
    """

    model_config = ConfigDict(extra="forbid")

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_entries: list[RawExperienceEntry] = Field(default_factory=list)
    education_entries: list[RawEducationEntry] = Field(default_factory=list)
    certifications: list[RawCertificationEntry] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
