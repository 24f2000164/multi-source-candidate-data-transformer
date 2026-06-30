"""Unit tests for transformer.parsers.resume.name_detector."""

from transformer.parsers.resume.name_detector import NameDetector
from transformer.parsers.resume.text_extractor import ExtractedText, TextBlock


def _page1_blocks(*lines: str) -> ExtractedText:
    blocks = [
        TextBlock(text=line, order=i, page_index=0, is_isolated=True)
        for i, line in enumerate(lines)
    ]
    return ExtractedText(plain_text="\n".join(lines), blocks=blocks)


class TestNameDetector:
    def test_top_block_heuristic_picks_correct_name(self) -> None:
        extracted = _page1_blocks("Jane Doe", "jane@example.com", "Skills")
        result = NameDetector().detect(extracted)
        assert result == ("Jane", "Doe")

    def test_proximity_heuristic_used_when_no_block_data(self) -> None:
        extracted = ExtractedText(
            plain_text="Jane Doe\njane@example.com\nSkills",
            blocks=[],
        )
        result = NameDetector().detect(extracted)
        assert result == ("Jane", "Doe")

    def test_header_line_excluded_from_name_candidates(self) -> None:
        extracted = ExtractedText(plain_text="Skills\nJane Doe\nPython", blocks=[])
        result = NameDetector().detect(extracted)
        assert result == ("Jane", "Doe")

    def test_email_looking_first_line_excluded(self) -> None:
        extracted = ExtractedText(
            plain_text="jane.doe@example.com\nJane Doe\nPython", blocks=[]
        )
        result = NameDetector().detect(extracted)
        assert result == ("Jane", "Doe")

    def test_no_name_found_returns_none(self) -> None:
        extracted = ExtractedText(
            plain_text="jane.doe@example.com\n555-123-4567\nSkills", blocks=[]
        )
        result = NameDetector().detect(extracted)
        assert result is None

    def test_three_word_name_supported(self) -> None:
        extracted = ExtractedText(plain_text="Mary Jane Watson\nSkills", blocks=[])
        result = NameDetector().detect(extracted)
        assert result == ("Mary", "Jane Watson")
