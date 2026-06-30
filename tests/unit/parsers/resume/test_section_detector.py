"""Unit tests for transformer.parsers.resume.section_detector."""

from transformer.parsers.resume.section_detector import SectionDetector, SectionName
from transformer.parsers.resume.text_extractor import ExtractedText, TextBlock


def _blocks(*lines: str) -> ExtractedText:
    blocks = [TextBlock(text=line, order=i) for i, line in enumerate(lines)]
    return ExtractedText(plain_text="\n".join(lines), blocks=blocks)


class TestSectionDetector:
    def test_detects_skills_section(self) -> None:
        extracted = _blocks("John Doe", "Skills", "Python, Java", "Education", "MIT")
        result = SectionDetector().detect(extracted)
        assert SectionName.SKILLS in result
        assert "Python, Java" in result[SectionName.SKILLS]

    def test_detects_all_expanded_aliases(self) -> None:
        aliases = {
            SectionName.SKILLS: "Tech Stack",
            SectionName.EXPERIENCE: "Employment History",
            SectionName.EDUCATION: "Academic Background",
            SectionName.CERTIFICATIONS: "Licenses",
            SectionName.LANGUAGES: "Language Proficiency",
        }
        for section, alias in aliases.items():
            extracted = _blocks(alias, "body content here")
            result = SectionDetector().detect(extracted)
            assert section in result

    def test_normalises_punctuation_case_and_whitespace(self) -> None:
        extracted = _blocks("  SKILLS:  ", "Python")
        result = SectionDetector().detect(extracted)
        assert SectionName.SKILLS in result

    def test_missing_section_absent_from_result(self) -> None:
        extracted = _blocks("John Doe", "Skills", "Python")
        result = SectionDetector().detect(extracted)
        assert SectionName.EXPERIENCE not in result

    def test_isolated_header_preferred_over_inline_text(self) -> None:
        # "skills" appearing mid-sentence (not its own block) must not be
        # treated as a header because it exceeds the max header word count.
        extracted = _blocks(
            "I have many skills relevant to this role and more words here",
            "Skills",
            "Python",
        )
        result = SectionDetector().detect(extracted)
        assert result[SectionName.SKILLS].strip() == "Python"

    def test_is_header_alias_helper(self) -> None:
        assert SectionDetector.is_header_alias("Skills") is True
        assert SectionDetector.is_header_alias("John Doe") is False
