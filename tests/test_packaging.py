"""Packaging metadata and distribution-surface tests."""

from pathlib import Path
import tomllib

import transformer
from transformer.cli import app

ROOT = Path(__file__).resolve().parents[1]


def _project_metadata() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        document = tomllib.load(stream)
    return document["project"]


def test_package_imports() -> None:
    assert transformer is not None
    assert app is not None


def test_release_metadata() -> None:
    project = _project_metadata()
    assert project["name"] == "candidate-data-transformer"
    assert project["version"] == "1.0.0"
    assert project["readme"] == "README.md"
    assert project["license"] == {"file": "LICENSE"}


def test_console_scripts_target_cli_app() -> None:
    scripts = _project_metadata()["scripts"]
    assert scripts["candidate-transformer"] == "transformer.cli:app"
    assert scripts["transformer"] == "transformer.cli:app"


def test_required_distribution_files_exist() -> None:
    required = (
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "docs/index.md",
    )
    assert all((ROOT / name).is_file() for name in required)


def test_license_is_mit() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in license_text


def test_pyproject_is_only_version_source() -> None:
    package_files = (ROOT / "src" / "transformer").rglob("*.py")
    assert all(
        "__version__" not in path.read_text(encoding="utf-8") for path in package_files
    )


def test_release_workflow_is_not_added() -> None:
    assert not (ROOT / ".github" / "workflows" / "release.yml").exists()
