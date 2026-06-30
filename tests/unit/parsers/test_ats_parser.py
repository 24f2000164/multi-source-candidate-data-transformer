"""Unit tests for transformer.parsers.ats_parser."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from typing import Any

import pytest

from transformer.models import DataSource
from transformer.parsers.ats_parser import ATSParser
from transformer.parsers.exceptions import (
    FileReadError,
    InvalidJSONError,
    MappingError,
    SchemaValidationError,
)
from transformer.parsers.parser_config import ParserConfig


def _write_json(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _minimal() -> dict[str, Any]:
    return {"first_name": "Alice", "last_name": "Smith"}


@pytest.fixture
def parser() -> ATSParser:
    return ATSParser()


@pytest.mark.unit
class TestATSParserHappyPath:
    def test_minimal_valid_file_parses(self, tmp_path: Path, parser: ATSParser) -> None:
        f = _write_json(tmp_path / "ats.json", _minimal())
        candidate = parser.parse(f)
        assert candidate.first_name == "Alice"
        assert candidate.last_name == "Smith"

    def test_full_valid_file_parses(self, tmp_path: Path, parser: ATSParser) -> None:
        data = {
            **_minimal(),
            "candidate_id": "ATS-1001",
            "email": "alice@example.com",
            "phone": "1234567890",
            "skills": ["Python", "FastAPI", "Docker"],
            "experience": [
                {
                    "company": "Acme Corp",
                    "title": "Software Engineer",
                    "start_date": "2022-06-01",
                    "end_date": "2024-01-01",
                    "description": "Built things.",
                }
            ],
            "education": [{"institution": "IIT Madras", "degree": "BS Data Science"}],
            "certifications": [{"name": "AWS Certified Developer"}],
            "languages": ["English", "Hindi"],
        }
        f = _write_json(tmp_path / "ats.json", data)
        candidate = parser.parse(f)
        assert candidate.external_id == "ATS-1001"
        assert candidate.contact is not None
        assert candidate.contact.email == "alice@example.com"
        assert len(candidate.experiences) == 1
        assert len(candidate.education) == 1
        assert len(candidate.certifications) == 1
        assert candidate.provenance["first_name"].source == DataSource.ATS


@pytest.mark.unit
class TestATSParserFileLevelErrors:
    def test_missing_file_raises_file_read_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        with pytest.raises(FileReadError):
            parser.parse(tmp_path / "does_not_exist.json")

    def test_wrong_extension_raises_file_read_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        f = tmp_path / "ats.txt"
        f.write_text(json.dumps(_minimal()), encoding="utf-8")
        with pytest.raises(FileReadError):
            parser.parse(f)

    def test_oversized_file_raises_file_read_error(self, tmp_path: Path) -> None:
        f = _write_json(tmp_path / "ats.json", _minimal())
        small_parser = ATSParser(config=ParserConfig(max_file_size_bytes=5))
        with pytest.raises(FileReadError):
            small_parser.parse(f)


@pytest.mark.unit
class TestATSParserMalformedJSON:
    def test_malformed_json_syntax_raises_invalid_json_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        f = tmp_path / "ats.json"
        f.write_text('{"first_name": "Alice", "last_name": ', encoding="utf-8")
        with pytest.raises(InvalidJSONError):
            parser.parse(f)

    def test_empty_file_raises_invalid_json_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        f = tmp_path / "ats.json"
        f.write_text("", encoding="utf-8")
        with pytest.raises(InvalidJSONError):
            parser.parse(f)

    def test_empty_json_object_raises_schema_validation_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        f = _write_json(tmp_path / "ats.json", {})
        with pytest.raises(SchemaValidationError):
            parser.parse(f)

    def test_truncated_fuzzed_json_raises_invalid_json_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        f = tmp_path / "ats.json"
        valid = json.dumps(_minimal())
        truncated = valid[: len(valid) // 2]
        f.write_text(truncated, encoding="utf-8")
        with pytest.raises(InvalidJSONError):
            parser.parse(f)

    @pytest.mark.parametrize(
        "garbage",
        [
            "{]",
            "[}",
            "{'first_name': 'Alice'}",  # single quotes, not valid JSON
            "first_name: Alice",
            "{,}",
            "NaN",
            '{"a": }',
        ],
    )
    def test_fuzzed_json_variants_raise_invalid_json_error(
        self, tmp_path: Path, parser: ATSParser, garbage: str
    ) -> None:
        f = tmp_path / "ats.json"
        f.write_text(garbage, encoding="utf-8")
        with pytest.raises((InvalidJSONError, SchemaValidationError)):
            parser.parse(f)


@pytest.mark.unit
class TestATSParserRequiredFields:
    def test_missing_first_name_raises_schema_validation_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = _minimal()
        del data["first_name"]
        f = _write_json(tmp_path / "ats.json", data)
        with pytest.raises(SchemaValidationError):
            parser.parse(f)

    def test_missing_last_name_raises_schema_validation_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = _minimal()
        del data["last_name"]
        f = _write_json(tmp_path / "ats.json", data)
        with pytest.raises(SchemaValidationError):
            parser.parse(f)

    def test_null_required_field_raises_schema_validation_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = {**_minimal(), "first_name": None}
        f = _write_json(tmp_path / "ats.json", data)
        with pytest.raises(SchemaValidationError):
            parser.parse(f)


@pytest.mark.unit
class TestATSParserInvalidNestedObjects:
    def test_invalid_email_raises_mapping_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = {**_minimal(), "email": "not-an-email"}
        f = _write_json(tmp_path / "ats.json", data)
        with pytest.raises(MappingError):
            parser.parse(f)

    def test_invalid_uuid_like_id_does_not_raise(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        """candidate_id is opaque external_id, not a UUID -- any string works."""
        data = {**_minimal(), "candidate_id": "not-a-valid-uuid"}
        f = _write_json(tmp_path / "ats.json", data)
        candidate = parser.parse(f)
        assert candidate.external_id == "not-a-valid-uuid"

    def test_experience_missing_required_field_raises_mapping_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = {**_minimal(), "experience": [{"title": "Engineer"}]}
        f = _write_json(tmp_path / "ats.json", data)
        with pytest.raises(MappingError):
            parser.parse(f)

    def test_invalid_date_format_raises_mapping_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = {
            **_minimal(),
            "experience": [
                {"company": "Acme", "title": "Eng", "start_date": "13/45/2099"}
            ],
        }
        f = _write_json(tmp_path / "ats.json", data)
        with pytest.raises(MappingError):
            parser.parse(f)


@pytest.mark.unit
class TestATSParserUnexpectedFields:
    def test_unexpected_top_level_field_ignored_not_raised(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = {**_minimal(), "favorite_pizza": "margherita"}
        f = _write_json(tmp_path / "ats.json", data)
        candidate = parser.parse(f)
        assert candidate.first_name == "Alice"

    def test_deeply_nested_unexpected_object_ignored(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        nested: dict[str, Any] = {"value": "leaf"}
        for _ in range(60):
            nested = {"child": nested}
        data = {**_minimal(), "weird_metadata": nested}
        f = _write_json(tmp_path / "ats.json", data)
        candidate = parser.parse(f)
        assert candidate.first_name == "Alice"


@pytest.mark.unit
class TestATSParserUnicodeAndEncoding:
    def test_unicode_names_parse_correctly(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = {"first_name": "\u00c9milie", "last_name": "M\u00fcller"}
        f = _write_json(tmp_path / "ats.json", data)
        candidate = parser.parse(f)
        assert candidate.first_name == "\u00c9milie"
        assert candidate.last_name == "M\u00fcller"

    def test_emoji_in_description_parses(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = {
            **_minimal(),
            "experience": [
                {
                    "company": "Acme",
                    "title": "Engineer",
                    "start_date": "2022-01-01",
                    "description": "Shipped features \U0001f680",
                }
            ],
        }
        f = _write_json(tmp_path / "ats.json", data)
        candidate = parser.parse(f)
        assert "\U0001f680" in (candidate.experiences[0].description or "")

    def test_utf8_bom_is_tolerated(self, tmp_path: Path, parser: ATSParser) -> None:
        f = tmp_path / "ats.json"
        content = json.dumps(_minimal())
        f.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
        candidate = parser.parse(f)
        assert candidate.first_name == "Alice"

    def test_malformed_utf8_bytes_raise_invalid_json_error(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        f = tmp_path / "ats.json"
        # 0xFF is never valid in any position of a UTF-8 byte sequence.
        f.write_bytes(b'{"first_name": "Alice\xff", "last_name": "Smith"}')
        with pytest.raises(InvalidJSONError):
            parser.parse(f)

    def test_windows_line_endings_parse_correctly(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        f = tmp_path / "ats.json"
        content = json.dumps(_minimal(), indent=2).replace("\n", "\r\n")
        f.write_text(content, encoding="utf-8", newline="")
        candidate = parser.parse(f)
        assert candidate.first_name == "Alice"


@pytest.mark.unit
class TestATSParserLargeInput:
    def test_many_skills_parses_successfully(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = {**_minimal(), "skills": [f"Skill{i}" for i in range(400)]}
        f = _write_json(tmp_path / "ats.json", data)
        candidate = parser.parse(f)
        assert len(candidate.skills) == 400

    def test_many_experience_entries_parses_successfully(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        data = {
            **_minimal(),
            "experience": [
                {
                    "company": f"Company{i}",
                    "title": "Engineer",
                    "start_date": "2020-01-01",
                    "end_date": "2021-01-01",
                }
                for i in range(150)
            ],
        }
        f = _write_json(tmp_path / "ats.json", data)
        candidate = parser.parse(f)
        assert len(candidate.experiences) == 150


@pytest.mark.unit
class TestATSParserConcurrency:
    def test_concurrent_parsing_is_safe_and_deterministic(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        """Parser holds no mutable state, so parallel parses of the same
        file must all succeed and produce equal (first_name, last_name,
        skills) tuples -- proving no shared-state corruption."""
        f = _write_json(
            tmp_path / "ats.json",
            {**_minimal(), "skills": ["Python", "FastAPI"]},
        )

        def _parse_once() -> tuple[str, str, list[str]]:
            candidate = parser.parse(f)
            return (candidate.first_name, candidate.last_name, candidate.skills)

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: _parse_once(), range(32)))

        assert len(results) == 32
        assert all(r == ("Alice", "Smith", ["Python", "FastAPI"]) for r in results)

    def test_concurrent_parsing_distinct_files_independent(
        self, tmp_path: Path, parser: ATSParser
    ) -> None:
        files = []
        for i in range(10):
            f = _write_json(
                tmp_path / f"ats_{i}.json",
                {"first_name": f"Person{i}", "last_name": "Test"},
            )
            files.append(f)

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(parser.parse, files))

        names = sorted(c.first_name for c in results)
        assert names == [f"Person{i}" for i in range(10)]
