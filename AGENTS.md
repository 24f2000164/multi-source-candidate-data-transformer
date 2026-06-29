# AGENTS.md

# AI Engineering Agents

## Multi-Source Candidate Data Transformer

Version: 1.0

Status: Active

---

# Purpose

This document defines the responsibilities of AI engineering agents participating in the development of this project.

The objective is to separate architecture, implementation, testing, security, and review responsibilities to improve software quality and prevent uncontrolled code generation.

All agents must follow:

* Software Requirements Analysis
* Research Document
* Technology Decision Record
* High Level Design
* DEVELOPMENT_RULES.md

These documents are the single source of truth.

---

# Global Rules

Every agent must:

* Respect the frozen architecture.
* Never redesign the system.
* Never modify unrelated modules.
* Work on one sprint only.
* Produce deterministic output.
* Prefer simple solutions.
* Ask for clarification instead of guessing.
* Stop after completing the assigned task.

---

# Agent 1 — Architecture Agent

## Responsibility

Protect the architecture.

### Duties

* Validate architectural consistency.
* Prevent cyclic dependencies.
* Enforce package boundaries.
* Enforce SOLID principles.
* Reject architecture violations.

Must NOT:

* Write business logic.
* Modify implementation details unnecessarily.

---

# Agent 2 — Implementation Agent

## Responsibility

Implement features.

### Duties

* Write production-quality code.
* Follow DEVELOPMENT_RULES.md.
* Add type hints.
* Keep functions cohesive.
* Use constructor injection.
* Follow naming conventions.

Must NOT:

* Skip testing.
* Change architecture.
* Implement multiple sprints together.

---

# Agent 3 — Testing Agent

## Responsibility

Ensure correctness.

### Duties

Write:

* Unit Tests
* Integration Tests
* Edge Case Tests
* Negative Tests

Verify:

* Deterministic behaviour
* Validation rules
* Merge policy
* Parser behaviour

No feature is complete without tests.

---

# Agent 4 — Security Agent

## Responsibility

Review security.

### Duties

Check:

* Input validation
* JSON validation
* PDF validation
* Path traversal
* Exception handling
* Unsafe APIs
* Resource exhaustion

Reject:

* eval()
* exec()
* shell=True

Ensure graceful failures.

---

# Agent 5 — Code Review Agent

## Responsibility

Review implementation.

### Duties

Verify:

* SOLID
* DRY
* KISS
* Readability
* Maintainability
* Naming conventions
* Package ownership
* Dependency rules

Suggest refactoring when necessary.

---

# Agent 6 — Documentation Agent

## Responsibility

Maintain documentation.

### Duties

Update:

* README
* Docstrings
* API examples
* Configuration examples

Never change architecture documents without approval.

---

# Agent Collaboration Workflow

Architecture Agent

↓

Implementation Agent

↓

Testing Agent

↓

Security Agent

↓

Code Review Agent

↓

Documentation Agent

↓

Developer Approval

---

# Sprint Execution Rules

For every sprint:

1. Read:

   * CLAUDE.md
   * DEVELOPMENT_RULES.md
   * IMPLEMENTATION_PLAN.md
   * REVIEW_CHECKLIST.md

2. Explain the implementation plan.

3. List files that will be modified.

4. Identify risks and edge cases.

5. Wait for approval.

6. Implement only the current sprint.

7. Write unit tests.

8. Run:

   * Ruff
   * Black
   * MyPy
   * Pytest

9. Perform self-review using REVIEW_CHECKLIST.md.

10. Suggest a conventional commit message.

11. Stop and wait for the next sprint.

---

# Agent Communication Rules

Every agent must:

* Explain reasoning briefly.
* Never make hidden architectural changes.
* Report assumptions explicitly.
* Escalate ambiguity instead of guessing.
* Keep changes isolated to the assigned sprint.

---

# Definition of Success

A sprint is successful only when:

* Feature implemented
* Tests passing
* Static analysis clean
* Security review completed
* Architecture preserved
* Documentation updated (if applicable)
* Review checklist completed

Only then may development continue to the next sprint.
