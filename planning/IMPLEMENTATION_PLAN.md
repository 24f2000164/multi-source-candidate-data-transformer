# IMPLEMENTATION_PLAN.md

# Multi-Source Candidate Data Transformer

## Implementation Roadmap

Version: 1.0

Status: Active

---

# Purpose

This document defines the implementation roadmap for the project.

Each sprint focuses on one feature only.

A sprint is considered complete only after:

* Implementation
* Unit Tests
* Static Analysis
* Self Review

are completed successfully.

Claude Code must never implement multiple sprints together.

---

# Sprint 0 — Project Bootstrap

## Goal

Initialize the production-ready project.

### Deliverables

* Repository structure
* Python packages
* pyproject.toml
* Ruff
* Black
* MyPy
* pytest
* Makefile
* README
* GitHub Actions
* Pre-commit hooks

### Tests

* Project imports successfully
* Tooling executes without errors

### Status

⬜ Not Started

---

# Sprint 1 — Domain Models

## Goal

Implement Pydantic domain models.

### Modules

* Candidate
* Experience
* Education
* Confidence
* Provenance

### Tests

* Model validation
* Invalid data
* Required fields
* Serialization

### Status

⬜ Not Started

---

# Sprint 2 — ATS Parser

## Goal

Implement structured ATS JSON parser.

### Features

* Read ATS JSON
* Validate schema
* Map to Canonical Model

### Tests

* Valid JSON
* Missing fields
* Invalid schema
* Malformed JSON

### Status

⬜ Not Started

---

# Sprint 3 — Resume Parser

## Goal

Implement Resume PDF parser.

### Features

* Read PDF
* Extract text
* Parse candidate information
* Produce Canonical Model

### Tests

* Valid PDF
* Empty PDF
* Corrupted PDF
* Missing sections

### Status

⬜ Not Started

---

# Sprint 4 — Normalization Engine

## Goal

Normalize extracted data.

### Features

* Email normalization
* Phone normalization
* Skill normalization
* Date normalization

### Tests

* Duplicate skills
* Invalid phone
* Mixed date formats

### Status

⬜ Not Started

---

# Sprint 5 — Merge Engine

## Goal

Generate Golden Candidate Record.

### Features

* Field priority
* Conflict resolution
* Provenance
* Merge policy

### Tests

* Matching data
* Conflicting data
* Missing data
* Null values

### Status

⬜ Not Started

---

# Sprint 6 — Confidence Engine

## Goal

Generate confidence scores.

### Features

* Field confidence
* Overall confidence

### Tests

* Single source
* Multiple source
* Conflict
* Invalid values

### Status

⬜ Not Started

---

# Sprint 7 — Validation Layer

## Goal

Validate complete pipeline.

### Features

* Input validation
* Canonical validation
* Output validation

### Tests

* Valid candidate
* Invalid candidate
* Missing mandatory fields

### Status

⬜ Not Started

---

# Sprint 8 — Projection Engine

## Goal

Support configurable output.

### Features

* Include fields
* Exclude fields
* Custom projection

### Tests

* Default config
* Custom config
* Invalid config

### Status

⬜ Not Started

---

# Sprint 9 — CLI Integration

## Goal

Connect complete pipeline.

### Features

* CLI
* End-to-end execution
* Output generation

### Tests

* End-to-end pipeline
* Invalid input
* Missing configuration

### Status

⬜ Not Started

---

# Sprint Completion Rules

A sprint is complete only if:

* Feature implemented
* Unit tests added
* Ruff passes
* Black passes
* MyPy passes
* Pytest passes
* Documentation updated
* Code reviewed

---

# Development Workflow

Implementation Plan

↓

Approval

↓

Implementation

↓

Unit Tests

↓

Static Analysis

↓

Review

↓

Commit

↓

Next Sprint
