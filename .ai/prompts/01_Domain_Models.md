# Sprint 01 – Domain Models

## Multi-Source Candidate Data Transformer

Sprint: 01

Feature: Domain Models

Status: Ready for Implementation

---

# Context

You are a Senior Python Software Engineer working on the Multi-Source Candidate Data Transformer project.

The architecture has already been finalized.

The following documents are the single source of truth and must be read before making any implementation decision.

1. CLAUDE.md
2. AGENTS.md
3. docs/DEVELOPMENT_RULES.md
4. docs/04_High_Level_Design.docx
5. docs/03_Technology_Decision_Record.docx
6. planning/IMPLEMENTATION_PLAN.md
7. planning/REVIEW_CHECKLIST.md

Do not redesign the architecture.

Do not introduce new packages.

Do not modify engineering decisions.

---

# Sprint Goal

Implement the complete domain model layer using Pydantic v2.

The domain models represent the Canonical Candidate Model used throughout the application.

This sprint only creates validated domain models.

No parsing.

No normalization.

No merge logic.

No CLI.

---

# Out of Scope

The following must NOT be implemented.

* ATS Parser
* Resume Parser
* Merge Engine
* Projection Engine
* Validation Engine
* Confidence Engine
* CLI
* Output Writer

---

# Files Allowed To Modify

Only modify:

src/transformer/models/

tests/unit/models/

If additional files are required, explain why before creating them.

---

# Functional Requirements

Implement the following models.

Candidate

Experience

Education

Certification

ContactInformation

Confidence

Provenance

Address (if required)

Common Enums (if required)

Every model must support validation.

Every model must support serialization.

Every model must be immutable wherever practical.

---

# Validation Requirements

Validate:

Email

Phone

Dates

Required Fields

Lists

Optional Fields

Default Values

Reject invalid data.

Produce meaningful validation errors.

---

# Non Functional Requirements

The implementation must be:

Deterministic

Thread Safe

Stateless

Production Ready

Strongly Typed

Easy to Extend

Easy to Test

Fully Documented

---

# Security Requirements

Never trust external input.

Validate every field.

Reject malformed data.

No unsafe deserialization.

No dynamic code execution.

No shell commands.

No unsafe file operations.

---

# Edge Cases

The implementation must correctly handle:

Missing email

Missing phone

Duplicate skills

Duplicate certifications

Empty experience

Empty education

Null values

Unicode names

Very long strings

Unexpected optional fields

Invalid email

Invalid phone number

Future employment dates

End date before start date

Malformed URLs

Invalid confidence values

---

# Error Handling

Use domain specific validation.

Return meaningful Pydantic validation errors.

Never silently ignore invalid data.

Avoid generic exceptions.

---

# Performance Requirements

Avoid unnecessary object creation.

Prefer immutable models.

Support efficient serialization.

Avoid duplicated validation logic.

---

# Code Standards

Mandatory

Python 3.12

Pydantic v2

Type hints

Docstrings

Constructor validation

Meaningful names

Small cohesive classes

No duplicate code

No TODO

No FIXME

---

# Testing Requirements

Write comprehensive unit tests.

Minimum tests:

Happy Path

Missing Required Field

Invalid Email

Invalid Phone

Invalid Dates

Serialization

Deserialization

Optional Fields

Edge Cases

Boundary Cases

Regression Tests

Target:

High branch coverage.

---

# Deliverables

Implement:

All domain models

Validation rules

Unit tests

Package exports

Public API

No business logic.

---

# Acceptance Criteria

The sprint is complete only if:

✓ All models implemented

✓ Validation implemented

✓ Serialization works

✓ Unit tests pass

✓ Ruff passes

✓ Black passes

✓ MyPy passes

✓ Pytest passes

✓ REVIEW_CHECKLIST completed

---

# Before Writing Code

First perform the following steps.

1. Read all project documents.

2. Summarize the architecture relevant to this sprint.

3. Explain the implementation strategy.

4. List every file you plan to modify.

5. Identify potential risks.

6. Identify missing assumptions.

7. Wait for my approval.

Do not write any code until approval is received.

---

# After Approval

After implementation:

Run Ruff.

Run Black.

Run MyPy.

Run Pytest.

Perform a self-review using planning/REVIEW_CHECKLIST.md.

Generate:

Implementation Summary

Files Modified

Test Summary

Known Limitations

Suggested Improvements

Conventional Commit Message

STOP

Do not continue to Sprint 02.
