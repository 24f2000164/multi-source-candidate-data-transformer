# DEVELOPMENT_RULES.md

# Development Standards

## Multi-Source Candidate Data Transformer

Version: 1.0

Status: Frozen

---

# Purpose

This document defines the mandatory engineering standards for the project.

These rules apply to all contributors, including AI coding assistants.

The objective is to ensure:

* Consistent architecture
* High code quality
* Secure implementation
* Deterministic behavior
* Production-ready maintainability

These rules are mandatory and must not be violated.

---

# 1. General Engineering Principles

The implementation shall follow:

* SOLID Principles
* DRY (Don't Repeat Yourself)
* KISS (Keep It Simple)
* Separation of Concerns
* Composition over Inheritance
* Configuration Driven Design
* Deterministic Processing

---

# 2. Architecture Rules

The architecture is frozen.

The implementation must follow the approved HLD.

Do NOT:

* Redesign the architecture
* Introduce unnecessary layers
* Create cyclic dependencies
* Move business logic into models
* Mix infrastructure with business logic

Every package owns exactly one responsibility.

---

# 3. Package Rules

Every package must:

* Have one responsibility
* Expose only its public API
* Be independently testable
* Avoid hidden side effects

Forbidden:

* Cross-package business logic
* Circular imports
* Tight coupling

---

# 4. Naming Convention

Packages

snake_case

Modules

snake_case

Functions

snake_case

Variables

snake_case

Classes

PascalCase

Constants

UPPER_CASE

Private Members

_prefix

---

# 5. Code Standards

Mandatory:

* Python 3.12+
* Type hints everywhere
* Docstrings for every public class and function
* Small cohesive functions
* Explicit return types
* Meaningful variable names

Avoid:

* Magic numbers
* Duplicate logic
* Long methods
* Deep nesting
* Wildcard imports

---

# 6. Dependency Injection

Always use Constructor Injection.

Do not instantiate dependencies inside business classes.

Prefer:

PipelineOrchestrator(
parser,
normalizer,
merge_engine,
validator,
)

Avoid:

PipelineOrchestrator()

↓

creates parser internally

---

# 7. Configuration Rules

Configuration must be external.

Use YAML.

Do not hardcode:

* file paths
* thresholds
* projection fields
* merge rules

Configuration must be validated before use.

---

# 8. Validation Rules

Validate at three levels:

1. Input Validation

2. Canonical Model Validation

3. Output Validation

Never trust external input.

---

# 9. Security Standards

Validate every external input.

Reject malformed JSON.

Validate PDF before parsing.

Sanitize file paths.

Do not use:

* eval()
* exec()
* shell=True

Limit maximum file size.

Handle parser failures gracefully.

Never expose stack traces to end users.

---

# 10. Error Handling

Use domain-specific exceptions.

Never silently ignore errors.

Every recoverable error must be logged.

Fatal errors must terminate gracefully.

Avoid generic Exception wherever possible.

---

# 11. Logging Standards

Use Python logging.

Log:

* Pipeline Start
* Pipeline End
* Parsing
* Merge
* Validation
* Errors

Log Levels

INFO

WARNING

ERROR

DEBUG

Never log sensitive data.

---

# 12. Testing Standards

Every feature must include tests.

Minimum tests:

* Happy Path
* Invalid Input
* Edge Cases
* Failure Scenario

Target:

High branch coverage.

No feature is complete without tests.

---

# 13. Static Analysis

Every sprint must pass:

* Ruff
* Black
* MyPy
* Pytest

No warnings should remain.

---

# 14. Documentation Standards

Every public class:

Docstring required.

Every public function:

Docstring required.

Every complex algorithm:

Short explanation.

Update README whenever public behavior changes.

---

# 15. Git Standards

One sprint = One commit.

Commit format:

feat(module): description

fix(module): description

refactor(module): description

test(module): description

docs(module): description

Keep commits focused.

---

# 16. Performance Guidelines

Avoid unnecessary object creation.

Prefer streaming over loading large files when possible.

Keep modules stateless.

Optimize only after correctness.

---

# 17. Definition of Done

A feature is complete only if:

✓ Implementation completed

✓ Unit tests added

✓ Ruff passes

✓ Black passes

✓ MyPy passes

✓ Pytest passes

✓ Logging added

✓ Error handling implemented

✓ Type hints complete

✓ Documentation updated

✓ Code reviewed

---

# 18. Code Review Checklist

Before completing any sprint verify:

* Architecture respected
* SOLID followed
* No duplicated logic
* Correct package ownership
* Dependency rules followed
* Edge cases handled
* Security validated
* Tests passing
* Static analysis passing

Only after all checks pass should the sprint be considered complete.

---

# Final Rule

When in doubt:

Do not guess.

Refer to:

* Software Requirements Analysis
* Research Document
* Technology Decision Record
* High Level Design

These documents are the single source of truth.

This document is mandatory for every implementation sprint.
