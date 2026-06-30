"""Builds the default ``RuleRegistry`` from a ``Config`` object.

Pipeline order: Schema -> Business -> Duplicate -> Cross-Field. Cross-field
rules (e.g. confidence/field consistency) run last so that duplicate
detection results are already available, which makes the combined report
easier to reason about and debug.
"""

from transformer.config.config_loader import Config
from transformer.validation.rule_registry import RuleRegistry
from transformer.validation.rules.business_rules import (
    EmailFormatRule,
    ExternalIdRule,
    PhoneFormatRule,
    UrlFormatRule,
)
from transformer.validation.rules.cross_field_rules import (
    ConfidenceFieldConsistencyRule,
    DateOrderRule,
)
from transformer.validation.rules.duplicate_rules import (
    DuplicateEducationRule,
    DuplicateExperienceRule,
)
from transformer.validation.rules.schema_rules import (
    ConfidenceValueRule,
    IdRule,
    RequiredFieldsRule,
    SchemaVersionRule,
    StringLengthRule,
    UnicodeConfusableRule,
)


def build_default_registry(config: Config | None = None) -> RuleRegistry:
    """Build the standard ``RuleRegistry`` used by the pipeline/CLI.

    Args:
        config: Optional validation config; when provided, ``max_length``
            and ``default_region`` are read from it.

    Returns:
        A ``RuleRegistry`` with all built-in rules, in the order
        Schema -> Business -> Duplicate -> Cross-Field.
    """
    max_length = 10_000
    default_region = "US"
    if config is not None:
        max_length = config.section("max_string_length", max_length)
        default_region = config.section("default_phone_region", default_region)

    return RuleRegistry(
        [
            # Schema
            RequiredFieldsRule(),
            SchemaVersionRule(),
            ConfidenceValueRule(),
            StringLengthRule(max_length=max_length),
            UnicodeConfusableRule(),
            IdRule(),
            # Business
            EmailFormatRule(),
            PhoneFormatRule(default_region=default_region),
            UrlFormatRule(),
            ExternalIdRule(),
            # Duplicate
            DuplicateExperienceRule(),
            DuplicateEducationRule(),
            # Cross-field (runs last; assumes duplicates already known)
            DateOrderRule(),
            ConfidenceFieldConsistencyRule(),
        ]
    )
