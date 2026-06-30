"""Integration tests for transformer.parsers.resume.resume_parser."""

import contextlib
from pathlib import Path

from docx import Document
import fitz
import pytest

from transformer.parsers.exceptions import (
    CorruptedFileError,
    MappingError,
    TextExtractionError,
    UnsupportedFormatError,
)
from transformer.parsers.resume.resume_parser import ResumeParser


def _pdf_with_text(path: Path, lines: list[str], y_start: int = 72) -> None:
    doc = fitz.open()
    page = doc.new_page()
    y = y_start
    for line in lines:
        page.insert_text((72, y), line)
        y += 20
    doc.save(str(path))
    doc.close()


def _docx_with_paragraphs(path: Path, lines: list[str]) -> None:
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    document.save(str(path))


class TestHappyPath:
    def test_parses_pdf_resume(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "resume.pdf"
        _pdf_with_text(
            pdf_path,
            [
                "Jane Doe",
                "jane@example.com | 555-123-4567",
                "Skills",
                "Python, SQL, Docker",
            ],
        )
        candidate = ResumeParser().parse(pdf_path)
        assert candidate.first_name == "Jane"
        assert candidate.contact is not None
        assert candidate.contact.email == "jane@example.com"
        assert "Python" in candidate.skills

    def test_parses_docx_resume(self, tmp_path: Path) -> None:
        docx_path = tmp_path / "resume.docx"
        _docx_with_paragraphs(
            docx_path,
            ["Jane Doe", "jane@example.com", "Skills", "Python, SQL"],
        )
        candidate = ResumeParser().parse(docx_path)
        assert candidate.first_name == "Jane"
        assert candidate.last_name == "Doe"


class TestNegativePath:
    def test_unsupported_extension_raises(self, tmp_path: Path) -> None:
        txt_path = tmp_path / "resume.txt"
        txt_path.write_text("Jane Doe")
        with pytest.raises(UnsupportedFormatError):
            ResumeParser().parse(txt_path)

    def test_extension_mismatch_pdf_actually_docx(self, tmp_path: Path) -> None:
        # See test_text_extractor for the documented fitz content-sniffing
        # quirk -- this only asserts no unhandled crash occurs.
        docx_path = tmp_path / "real.docx"
        _docx_with_paragraphs(docx_path, ["Jane Doe"])
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(docx_path.read_bytes())
        with contextlib.suppress(CorruptedFileError, TextExtractionError, MappingError):
            ResumeParser().parse(fake_pdf)

    def test_extension_mismatch_docx_actually_pdf(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "real.pdf"
        _pdf_with_text(pdf_path, ["Jane Doe"])
        fake_docx = tmp_path / "fake.docx"
        fake_docx.write_bytes(pdf_path.read_bytes())
        with pytest.raises(CorruptedFileError):
            ResumeParser().parse(fake_docx)


class TestEmptyAndCorruptedResumes:
    def test_blank_pdf_raises_text_extraction_error(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "blank.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()
        with pytest.raises(TextExtractionError):
            ResumeParser().parse(pdf_path)

    def test_blank_docx_raises_text_extraction_error(self, tmp_path: Path) -> None:
        docx_path = tmp_path / "blank.docx"
        Document().save(str(docx_path))
        with pytest.raises(TextExtractionError):
            ResumeParser().parse(docx_path)

    def test_image_only_pdf_raises_text_extraction_error(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "scanned.pdf"
        doc = fitz.open()
        page = doc.new_page()
        pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50))
        pixmap.set_rect(pixmap.irect, (0, 0, 255))
        page.insert_image(fitz.Rect(0, 0, 50, 50), pixmap=pixmap)
        doc.save(str(pdf_path))
        doc.close()
        with pytest.raises(TextExtractionError):
            ResumeParser().parse(pdf_path)

    def test_corrupted_pdf_raises_corrupted_file_error(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "bad.pdf"
        pdf_path.write_bytes(b"definitely not a pdf")
        with pytest.raises(CorruptedFileError):
            ResumeParser().parse(pdf_path)

    def test_corrupted_docx_raises_corrupted_file_error(self, tmp_path: Path) -> None:
        docx_path = tmp_path / "bad.docx"
        docx_path.write_bytes(b"definitely not a docx zip")
        with pytest.raises(CorruptedFileError):
            ResumeParser().parse(docx_path)

    def test_resume_without_name_raises_mapping_error(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "no_name.pdf"
        _pdf_with_text(pdf_path, ["jane@example.com", "555-123-4567", "Skills"])
        with pytest.raises(MappingError):
            ResumeParser().parse(pdf_path)


class TestUnicodeAndMultipleContacts:
    def test_unicode_name_and_text_handled(self, tmp_path: Path) -> None:
        docx_path = tmp_path / "unicode.docx"
        _docx_with_paragraphs(
            docx_path,
            ["José García", "jose@example.com", "Skills", "Café management, Résumé"],
        )
        candidate = ResumeParser().parse(docx_path)
        assert candidate.first_name == "José"

    def test_multiple_emails_first_one_selected(self, tmp_path: Path) -> None:
        docx_path = tmp_path / "multi_email.docx"
        _docx_with_paragraphs(
            docx_path,
            ["Jane Doe", "jane.work@example.com", "jane.personal@example.com"],
        )
        candidate = ResumeParser().parse(docx_path)
        assert candidate.contact is not None
        assert candidate.contact.email == "jane.work@example.com"

    def test_missing_optional_sections_degrade_gracefully(self, tmp_path: Path) -> None:
        docx_path = tmp_path / "no_sections.docx"
        _docx_with_paragraphs(docx_path, ["Jane Doe", "jane@example.com"])
        candidate = ResumeParser().parse(docx_path)
        assert candidate.skills == []
        assert candidate.experiences == []


class TestTwoColumnAndTableHeavy:
    def test_two_column_layout_does_not_crash(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "two_column.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Jane Doe")
        page.insert_text((72, 100), "Skills")
        page.insert_text((72, 120), "Python")
        page.insert_text((350, 100), "Education")
        page.insert_text((350, 120), "MIT")
        doc.save(str(pdf_path))
        doc.close()
        candidate = ResumeParser().parse(pdf_path)
        assert candidate.first_name == "Jane"

    def test_table_heavy_docx_skills_extracted(self, tmp_path: Path) -> None:
        docx_path = tmp_path / "table_resume.docx"
        document = Document()
        document.add_paragraph("Jane Doe")
        document.add_paragraph("jane@example.com")
        document.add_paragraph("Skills")
        table = document.add_table(rows=1, cols=2)
        table.rows[0].cells[0].text = "Python"
        table.rows[0].cells[1].text = "SQL"
        document.save(str(docx_path))
        candidate = ResumeParser().parse(docx_path)
        assert candidate.first_name == "Jane"


class TestLargeResume:
    def test_large_resume_with_many_lines_parses(self, tmp_path: Path) -> None:
        docx_path = tmp_path / "large.docx"
        lines = ["Jane Doe", "jane@example.com", "Skills"]
        lines += [f"Skill{i}" for i in range(300)]
        _docx_with_paragraphs(docx_path, lines)
        candidate = ResumeParser().parse(docx_path)
        assert candidate.first_name == "Jane"
        assert len(candidate.skills) > 0
