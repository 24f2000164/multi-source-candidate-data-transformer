"""Public API for the transformer.validation package.

Example::

    from transformer.validation import ValidationEngine, build_default_registry
"""

from transformer.validation.default_registry import build_default_registry
from transformer.validation.exceptions import DuplicateRuleNameError, ValidationEngineError
from transformer.validation.report import ValidationReport
from transformer.validation.rule import Severity, ValidationIssue, ValidationRule
from transformer.validation.rule_registry import RuleRegistry
from transformer.validation.validation_engine import ValidationEngine

__all__ = [
    "DuplicateRuleNameError",
    "RuleRegistry",
    "Severity",
    "ValidationEngine",
    "ValidationEngineError",
    "ValidationIssue",
    "ValidationReport",
    "ValidationRule",
    "build_default_registry",
]
