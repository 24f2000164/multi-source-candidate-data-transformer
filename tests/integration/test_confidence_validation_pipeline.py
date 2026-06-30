"""Integration tests across ConfidenceEngine + ValidationEngine.

Covers Sprint 06/07 edge cases end-to-end: single-source candidates, empty
candidates, merged candidates with conflicts, invalid config, and basic
performance sanity for the duplicate rule.
"""

from datetime import date
from pathlib import Path

import pytest

from transformer.config.config_loader import ConfigLoader
from transformer.config.exceptions import ConfigError
from transformer.confidence.confidence_engine import ConfidenceEngine, build_strategies
from transformer.confidence.merge_metadata import (
    StaticMergeMetadata,
    _FieldMergeView,
    from_single_source,
)
from transformer.models import Candidate, ContactInfo, DataSource, WorkExperience
from transformer.validation.default_registry import build_default_registry
from transformer.validation.rule_registry import RuleRegistry
from transformer.validation.validation_engine import ValidationEngine

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def _confidence_engine() -> ConfidenceEngine:
    loader = ConfigLoader()
    config = loader.load(_CONFIG_DIR / "confidence_rules.yaml")
    strategies = build_strategies(config.section("strategy_order"))
    source_weights = {
        DataSource(k): v for k, v in config.section("source_weights").items()
    }
    return ConfidenceEngine(
        strategies=strategies,
        source_weights=source_weights,
        field_weights=config.section("field_weights"),
        scored_fields=tuple(config.section("scored_fields")),
        config_version=config.version,
    )


def _validation_engine() -> ValidationEngine:
    loader = ConfigLoader()
    config = loader.load(_CONFIG_DIR / "validation_rules.yaml")
    return ValidationEngine(
        build_default_registry(config), config_version=config.version
    )


def test_ats_only_candidate_pipeline() -> None:
    candidate = Candidate(
        first_name="Jane",
        last_name="Doe",
        contact=ContactInfo(email="jane@example.com"),
    )
    metadata = from_single_source(DataSource.ATS)

    scored, confidence_report = _confidence_engine().run(candidate, metadata)
    validation_report = _validation_engine().run(scored)

    assert scored.confidence is not None
    assert confidence_report.overall_score > 0.0
    assert validation_report.is_valid is True


def test_resume_only_candidate_pipeline() -> None:
    candidate = Candidate(first_name="John", last_name="Smith")
    metadata = from_single_source(DataSource.RESUME)

    scored, confidence_report = _confidence_engine().run(candidate, metadata)
    validation_report = _validation_engine().run(scored)

    assert scored.confidence is not None
    assert confidence_report.overall_score >= 0.0
    assert validation_report.execution_time_ms >= 0.0


def test_merged_candidate_with_conflict_reflects_penalty() -> None:
    candidate = Candidate(first_name="Jane", last_name="Doe")
    conflicted_metadata = StaticMergeMetadata(
        _fields={
            "first_name": _FieldMergeView(
                conflict=True,
                contributing_sources=(DataSource.ATS,),
                sources_considered=(DataSource.ATS, DataSource.RESUME),
            )
        }
    )
    agreeing_metadata = StaticMergeMetadata(
        _fields={
            "first_name": _FieldMergeView(
                conflict=False,
                contributing_sources=(DataSource.ATS, DataSource.RESUME),
                sources_considered=(DataSource.ATS, DataSource.RESUME),
            )
        }
    )

    engine = _confidence_engine()
    _, conflicted_report = engine.run(candidate, conflicted_metadata)
    _, agreeing_report = engine.run(candidate, agreeing_metadata)

    assert (
        conflicted_report.field_scores["first_name"].score
        < agreeing_report.field_scores["first_name"].score
    )


def test_merged_candidate_with_injected_bad_data_flagged_by_validation() -> None:
    candidate = Candidate(
        first_name="Jane",
        last_name="Doe",
        external_id="bad id with spaces!!",
        experiences=[
            WorkExperience(company="Acme", title="Eng", start_date=date(2020, 1, 1)),
            WorkExperience(company="ACME", title="eng", start_date=date(2020, 1, 1)),
        ],
    )
    report = _validation_engine().run(candidate)
    assert report.is_valid is False
    rule_names = {issue.rule_name for issue in report.issues}
    assert "external_id_format" in rule_names
    assert "duplicate_experience" in rule_names


def test_empty_candidate_both_engines_no_op_gracefully() -> None:
    candidate = Candidate(first_name="Empty", last_name="Candidate")
    metadata = from_single_source(DataSource.ATS)

    scored, confidence_report = _confidence_engine().run(candidate, metadata)
    validation_report = _validation_engine().run(scored)

    assert confidence_report.overall_score >= 0.0
    assert isinstance(validation_report.is_valid, bool)


def test_invalid_merge_metadata_does_not_raise() -> None:
    candidate = Candidate(first_name="Jane", last_name="Doe")
    # conflict flag for a field key with no corresponding model field.
    metadata = StaticMergeMetadata(
        _fields={
            "totally_unknown_field": _FieldMergeView(
                conflict=True,
                contributing_sources=(DataSource.ATS,),
                sources_considered=(DataSource.ATS,),
            )
        }
    )
    scored, report = _confidence_engine().run(candidate, metadata)
    assert scored.confidence is not None
    assert report.overall_score >= 0.0


def test_two_hundred_experience_candidate_duplicate_rule_runs_quickly() -> None:
    import time

    experiences = [
        WorkExperience(
            company=f"Company {i}", title="Engineer", start_date=date(2020, 1, 1)
        )
        for i in range(200)
    ]
    candidate = Candidate(
        first_name="Jane", last_name="Doe", experiences=experiences
    )
    start = time.perf_counter()
    report = _validation_engine().run(candidate)
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0
    assert "duplicate_experience" not in {i.rule_name for i in report.errors}


def test_config_loader_raises_typed_error_for_bad_config(tmp_path: Path) -> None:
    bad_config = tmp_path / "broken.yaml"
    bad_config.write_text("foo: bar\n", encoding="utf-8")  # missing version
    with pytest.raises(ConfigError):
        ConfigLoader().load(bad_config)


def test_empty_rule_registry_produces_valid_report() -> None:
    engine = ValidationEngine(RuleRegistry([]))
    report = engine.run(Candidate(first_name="Jane", last_name="Doe"))
    assert report.is_valid is True
    assert report.issues == ()
