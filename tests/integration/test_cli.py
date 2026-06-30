"""CLI boundary integration tests for output and centralized errors."""

import json
from pathlib import Path

from typer.testing import CliRunner

from transformer.cli import app
from transformer.models import Candidate

runner = CliRunner()


def test_project_command_writes_json_output(tmp_path: Path) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(
        Candidate(first_name="Jane", last_name="Doe").model_dump_json(),
        encoding="utf-8",
    )
    output_path = tmp_path / "result.json"

    result = runner.invoke(
        app,
        [
            "project",
            str(candidate_path),
            "--format",
            "canonical",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["projection"]["first_name"] == "Jane"


def test_unknown_projection_prints_safe_stderr(tmp_path: Path) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(
        Candidate(first_name="Jane", last_name="Doe").model_dump_json(),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["project", str(candidate_path), "--format", "unknown"],
    )

    assert result.exit_code != 0
    assert "Unknown projection format" in result.stderr
    assert "Traceback" not in result.stderr
