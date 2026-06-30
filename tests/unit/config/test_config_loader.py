"""Unit tests for transformer.config.config_loader.ConfigLoader."""

from pathlib import Path

from pydantic import ValidationError
import pytest

from transformer.config.config_loader import ConfigLoader
from transformer.config.exceptions import ConfigError


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_valid_yaml(tmp_path: Path) -> None:
    path = _write(tmp_path, "ok.yaml", "version: '1.0'\nfoo: bar\n")
    config = ConfigLoader().load(path)
    assert config.version == "1.0"
    assert config.section("foo") == "bar"


def test_caches_within_loader_instance(tmp_path: Path) -> None:
    path = _write(tmp_path, "ok.yaml", "version: '1.0'\nfoo: bar\n")
    loader = ConfigLoader()
    first = loader.load(path)
    path.write_text("version: '1.0'\nfoo: changed\n", encoding="utf-8")
    second = loader.load(path)
    assert first is second
    assert second.section("foo") == "bar"


def test_clear_cache_forces_reload(tmp_path: Path) -> None:
    path = _write(tmp_path, "ok.yaml", "version: '1.0'\nfoo: bar\n")
    loader = ConfigLoader()
    loader.load(path)
    path.write_text("version: '1.0'\nfoo: changed\n", encoding="utf-8")
    loader.clear_cache()
    reloaded = loader.load(path)
    assert reloaded.section("foo") == "changed"


def test_fresh_loader_instances_do_not_share_cache(tmp_path: Path) -> None:
    path = _write(tmp_path, "ok.yaml", "version: '1.0'\nfoo: bar\n")
    ConfigLoader().load(path)
    path.write_text("version: '1.0'\nfoo: changed\n", encoding="utf-8")
    fresh = ConfigLoader().load(path)
    assert fresh.section("foo") == "changed"


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        ConfigLoader().load(tmp_path / "missing.yaml")


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    path = _write(tmp_path, "bad.yaml", "version: '1.0'\nfoo: [unterminated\n")
    with pytest.raises(ConfigError):
        ConfigLoader().load(path)


def test_missing_version_key_raises(tmp_path: Path) -> None:
    path = _write(tmp_path, "noversion.yaml", "foo: bar\n")
    with pytest.raises(ConfigError):
        ConfigLoader().load(path)


def test_version_mismatch_raises(tmp_path: Path) -> None:
    path = _write(tmp_path, "future.yaml", "version: '99.0'\nfoo: bar\n")
    with pytest.raises(ConfigError):
        ConfigLoader(current_version="1.0", minimum_supported_version="1.0").load(path)


def test_config_object_is_immutable(tmp_path: Path) -> None:
    path = _write(tmp_path, "ok.yaml", "version: '1.0'\nfoo: bar\n")
    config = ConfigLoader().load(path)
    with pytest.raises(ValidationError):
        config.version = "2.0"
