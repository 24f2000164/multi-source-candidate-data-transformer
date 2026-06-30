# Contributing

## Setup

```bash
python -m pip install -e ".[dev]"
pre-commit install
```

Python 3.12 or newer is required.

## Workflow

1. Read `AGENTS.md`, `CLAUDE.md`, `docs/DEVELOPMENT_RULES.md`, and the current
   sprint plan.
2. Keep changes within one approved sprint and preserve package boundaries.
3. Add happy-path, negative, edge-case, and failure tests.
4. Run Ruff, Black, MyPy, and Pytest.
5. Complete `planning/REVIEW_CHECKLIST.md`.

Do not change frozen architecture documents without approval. Do not add
business logic to the CLI, models, or configuration loaders.

## Commit messages

Use a focused conventional commit:

```text
feat(module): concise description
fix(module): concise description
docs(module): concise description
test(module): concise description
```

## Pull requests

Describe the sprint, changed files, risks, test results, and any known
limitations. Never include secrets, candidate personal data, or generated build
artifacts.
