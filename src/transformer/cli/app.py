"""Typer command-line interface and application composition root."""

from collections.abc import Callable
import json
from pathlib import Path
from typing import Annotated, Any

from pydantic_core import to_jsonable_python
import typer

from transformer.application import ApplicationResult, ApplicationService
from transformer.cli.error_handler import handle_cli_error
from transformer.confidence.confidence_engine import ConfidenceEngine, build_strategies
from transformer.config.config_loader import ConfigLoader
from transformer.config.loader import DEFAULT_CONFIG_DIR
from transformer.config.skill_aliases import load_skill_aliases
from transformer.merge.merge_engine import MergeEngine
from transformer.models import DataSource
from transformer.normalizers.normalization_engine import NormalizationEngine
from transformer.parsers.ats_parser import ATSParser
from transformer.parsers.resume.resume_parser import ResumeParser
from transformer.pipeline.pipeline import Pipeline
from transformer.projection import (
    AssignmentProjection,
    CanonicalProjection,
    ProjectionEngine,
    ProjectionRegistry,
)
from transformer.validation.default_registry import build_default_registry
from transformer.validation.validation_engine import ValidationEngine

app = typer.Typer(help="Transform ATS and resume data into candidate records.")


@app.command()
def parse(
    file_path: Annotated[Path, typer.Argument(help="ATS JSON or resume PDF/DOCX.")],
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    debug: Annotated[bool, typer.Option("--debug")] = False,
) -> None:
    """Parse and process one ATS or resume source."""
    _invoke(lambda service: service.parse(file_path), output, debug)


@app.command()
def merge(
    ats_path: Annotated[Path, typer.Argument(help="ATS JSON path.")],
    resume_path: Annotated[Path, typer.Argument(help="Resume PDF/DOCX path.")],
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    debug: Annotated[bool, typer.Option("--debug")] = False,
) -> None:
    """Parse, normalize, and merge ATS and resume sources."""
    _invoke(lambda service: service.merge(ats_path, resume_path), output, debug)


@app.command()
def validate(
    candidate_path: Annotated[Path, typer.Argument(help="Canonical candidate JSON.")],
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    debug: Annotated[bool, typer.Option("--debug")] = False,
) -> None:
    """Validate an existing canonical candidate record."""
    _invoke(lambda service: service.validate(candidate_path), output, debug)


@app.command()
def project(
    candidate_path: Annotated[Path, typer.Argument(help="Canonical candidate JSON.")],
    format_name: Annotated[str, typer.Option("--format")] = "canonical",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    debug: Annotated[bool, typer.Option("--debug")] = False,
) -> None:
    """Project an existing candidate into a named output format."""
    _invoke(lambda service: service.project(candidate_path, format_name), output, debug)


@app.command()
def transform(
    ats_path: Annotated[Path, typer.Argument(help="ATS JSON path.")],
    resume_path: Annotated[Path, typer.Argument(help="Resume PDF/DOCX path.")],
    format_name: Annotated[str, typer.Option("--format")] = "canonical",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    debug: Annotated[bool, typer.Option("--debug")] = False,
) -> None:
    """Run the complete two-source transformation pipeline."""
    _invoke(
        lambda service: service.transform(ats_path, resume_path, format_name),
        output,
        debug,
    )


def _invoke(
    operation: Callable[[ApplicationService], ApplicationResult],
    output: Path | None,
    debug: bool,
) -> None:
    try:
        result = operation(build_application_service())
        rendered = json.dumps(_jsonable(result), indent=2, ensure_ascii=False)
        if output is None:
            typer.echo(rendered)
        else:
            output.write_text(f"{rendered}\n", encoding="utf-8")
    except Exception as error:
        handle_cli_error(error, debug=debug)
    if result.exit_code != 0:
        raise typer.Exit(code=result.exit_code)


def build_application_service() -> ApplicationService:
    """Build the default production application graph for the CLI."""
    loader = ConfigLoader()
    confidence_config = loader.load(DEFAULT_CONFIG_DIR / "confidence_rules.yaml")
    validation_config = loader.load(DEFAULT_CONFIG_DIR / "validation_rules.yaml")

    source_weights = {
        DataSource(name): weight
        for name, weight in confidence_config.section("source_weights").items()
    }
    confidence_engine = ConfidenceEngine(
        strategies=build_strategies(confidence_config.section("strategy_order")),
        source_weights=source_weights,
        field_weights=confidence_config.section("field_weights"),
        scored_fields=tuple(confidence_config.section("scored_fields")),
        config_version=confidence_config.version,
    )
    validation_engine = ValidationEngine(
        build_default_registry(validation_config),
        config_version=validation_config.version,
    )
    projection_engine = ProjectionEngine(
        ProjectionRegistry(
            {
                "canonical": CanonicalProjection(),
                "assignment": AssignmentProjection(config_loader=loader),
            }
        )
    )
    return ApplicationService(
        pipeline=Pipeline(),
        ats_parser=ATSParser(),
        resume_parser=ResumeParser(),
        normalization_engine=NormalizationEngine(load_skill_aliases()),
        merge_engine=MergeEngine(),
        confidence_engine=confidence_engine,
        validation_engine=validation_engine,
        projection_engine=projection_engine,
    )


def _jsonable(value: object) -> Any:
    return to_jsonable_python(value)
