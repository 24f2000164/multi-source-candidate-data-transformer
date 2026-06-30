"""Unit tests for transformer.parsers.file_validator."""

import os
import sys
from pathlib import Path

import pytest

from transformer.parsers.exceptions import FileReadError
from transformer.parsers.file_validator import FileValidator
from transformer.parsers.parser_config import ParserConfig


@pytest.fixture
def validator() -> FileValidator:
    return FileValidator()


@pytest.fixture
def config() -> ParserConfig:
    return ParserConfig()


@pytest.mark.unit
class TestFileValidatorHappyPath:
    def test_valid_json_file_passes(
        self, tmp_path: Path, validator: FileValidator, config: ParserConfig
    ) -> None:
        f = tmp_path / "ats.json"
        f.write_text('{"a": 1}', encoding="utf-8")
        validator.validate(f, config)  # should not raise


@pytest.mark.unit
class TestFileValidatorMissingOrWrongType:
    def test_missing_file_raises(
        self, tmp_path: Path, validator: FileValidator, config: ParserConfig
    ) -> None:
        f = tmp_path / "does_not_exist.json"
        with pytest.raises(FileReadError, match="not found"):
            validator.validate(f, config)

    def test_directory_instead_of_file_raises(
        self, tmp_path: Path, validator: FileValidator, config: ParserConfig
    ) -> None:
        d = tmp_path / "a_directory.json"
        d.mkdir()
        with pytest.raises(FileReadError, match="regular file"):
            validator.validate(d, config)


@pytest.mark.unit
class TestFileValidatorExtension:
    def test_disallowed_extension_raises(
        self, tmp_path: Path, validator: FileValidator, config: ParserConfig
    ) -> None:
        f = tmp_path / "ats.txt"
        f.write_text("{}", encoding="utf-8")
        with pytest.raises(FileReadError, match="extension"):
            validator.validate(f, config)

    def test_no_extension_raises(
        self, tmp_path: Path, validator: FileValidator, config: ParserConfig
    ) -> None:
        f = tmp_path / "ats"
        f.write_text("{}", encoding="utf-8")
        with pytest.raises(FileReadError, match="extension"):
            validator.validate(f, config)


@pytest.mark.unit
class TestFileValidatorSize:
    def test_oversized_file_raises(
        self, tmp_path: Path, validator: FileValidator
    ) -> None:
        f = tmp_path / "huge.json"
        f.write_text('{"a": "' + ("x" * 1000) + '"}', encoding="utf-8")
        tiny_config = ParserConfig(max_file_size_bytes=10)
        with pytest.raises(FileReadError, match="exceeds maximum"):
            validator.validate(f, tiny_config)

    def test_file_at_exact_limit_passes(
        self, tmp_path: Path, validator: FileValidator
    ) -> None:
        f = tmp_path / "exact.json"
        content = "{}"
        f.write_text(content, encoding="utf-8")
        exact_config = ParserConfig(max_file_size_bytes=len(content))
        validator.validate(f, exact_config)  # should not raise


@pytest.mark.unit
class TestFileValidatorPathTraversal:
    def test_relative_path_with_parent_segments_resolves_safely(
        self, tmp_path: Path, validator: FileValidator, config: ParserConfig
    ) -> None:
        nested = tmp_path / "sub"
        nested.mkdir()
        target = tmp_path / "ats.json"
        target.write_text("{}", encoding="utf-8")
        traversal_path = nested / ".." / "ats.json"
        validator.validate(traversal_path, config)  # resolves to target, passes


@pytest.mark.unit
class TestFileValidatorPermissions:
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="POSIX permission bits are not enforced on Windows",
    )
    def test_unreadable_file_raises_file_read_error(
        self, tmp_path: Path, validator: FileValidator, config: ParserConfig
    ) -> None:
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            pytest.skip("Running as root: permission bits are not enforced")

        f = tmp_path / "ats.json"
        f.write_text("{}", encoding="utf-8")
        f.chmod(0o000)
        try:
            with pytest.raises(FileReadError):
                validator.validate(f, config)
        finally:
            f.chmod(0o644)