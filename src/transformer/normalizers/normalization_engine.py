"""NormalizationEngine: applies all normalizers to a single ``Candidate``,
returning a new, normalized ``Candidate``.

``Candidate`` (and its nested models) are frozen, so normalization always
produces a new instance via ``model_copy(update=...)`` rather than mutating
in place. The engine is idempotent: running it twice on an already
normalized candidate produces the same result (verified in
``tests/unit/normalizers/test_normalization_engine.py``).
"""

from transformer.models import (
    Candidate,
    Certification,
    ContactInfo,
    Education,
    WorkExperience,
)
from transformer.normalizers.email_normalizer import normalize_email
from transformer.normalizers.phone_normalizer import normalize_phone
from transformer.normalizers.skill_normalizer import normalize_skills
from transformer.normalizers.string_normalizer import clean, title_case_name


class NormalizationEngine:
    """Applies string/email/phone/skill normalization to a ``Candidate``."""

    def __init__(
        self,
        skill_alias_map: dict[str, str] | None = None,
        default_phone_region: str = "US",
    ) -> None:
        """Initialise the engine.

        Args:
            skill_alias_map: Alias map used by the skill normalizer (see
                ``transformer.config.skill_aliases.load_skill_aliases``).
                ``None`` disables alias resolution (casing/dedup only).
            default_phone_region: ISO 3166-1 alpha-2 region used to resolve
                phone numbers that lack an explicit ``+`` country code.
        """
        self._skill_alias_map = skill_alias_map
        self._default_phone_region = default_phone_region

    def normalize(self, candidate: Candidate) -> Candidate:
        """Normalize a single ``Candidate``.

        Args:
            candidate: The candidate to normalize.

        Returns:
            A new, normalized ``Candidate`` instance. ``id``, ``provenance``,
            ``confidence``, and ``schema_version`` are preserved unchanged.
        """
        updates: dict[str, object] = {
            "first_name": title_case_name(clean(candidate.first_name)),
            "last_name": title_case_name(clean(candidate.last_name)),
            "skills": normalize_skills(candidate.skills, self._skill_alias_map),
            "languages": [clean(lang) for lang in candidate.languages],
        }
        if candidate.contact is not None:
            updates["contact"] = self._normalize_contact(candidate.contact)
        if candidate.experiences:
            updates["experiences"] = [
                self._normalize_experience(exp) for exp in candidate.experiences
            ]
        if candidate.education:
            updates["education"] = [
                self._normalize_education(edu) for edu in candidate.education
            ]
        if candidate.certifications:
            updates["certifications"] = [
                self._normalize_certification(cert) for cert in candidate.certifications
            ]
        return candidate.model_copy(update=updates)

    def _normalize_contact(self, contact: ContactInfo) -> ContactInfo:
        updates: dict[str, object] = {}
        if contact.email is not None:
            updates["email"] = normalize_email(str(contact.email))
        if contact.phone is not None:
            updates["phone"] = normalize_phone(
                contact.phone, self._default_phone_region
            )
        if contact.location is not None:
            updates["location"] = clean(contact.location)
        return contact.model_copy(update=updates) if updates else contact

    def _normalize_experience(self, experience: WorkExperience) -> WorkExperience:
        updates: dict[str, object] = {
            "company": clean(experience.company),
            "title": clean(experience.title),
            "skills": normalize_skills(experience.skills, self._skill_alias_map),
        }
        if experience.description is not None:
            updates["description"] = clean(experience.description)
        return experience.model_copy(update=updates)

    def _normalize_education(self, education: Education) -> Education:
        updates: dict[str, object] = {
            "institution": clean(education.institution),
            "degree": clean(education.degree),
        }
        if education.field_of_study is not None:
            updates["field_of_study"] = clean(education.field_of_study)
        return education.model_copy(update=updates)

    def _normalize_certification(self, certification: Certification) -> Certification:
        updates: dict[str, object] = {"name": clean(certification.name)}
        if certification.issuer is not None:
            updates["issuer"] = clean(certification.issuer)
        return certification.model_copy(update=updates)
