"""Enumeration types for the canonical candidate domain model."""

from enum import StrEnum


class DataSource(StrEnum):
    """Identifies the origin system of an extracted data field.

    Inheriting from ``StrEnum`` ensures values are JSON-serialisable without a
    custom encoder.

    Attributes:
        ATS: Applicant Tracking System JSON record.
        RESUME: Candidate PDF resume.
    """

    ATS = "ATS"
    RESUME = "RESUME"
