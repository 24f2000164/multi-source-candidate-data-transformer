# Candidate Data Transformer

A production-inspired, multi-source candidate data transformation pipeline built
for the Eightfold AI engineering assignment.

The system ingests heterogeneous candidate data from an **ATS JSON** record and a
**Resume PDF**, resolves conflicts, normalises fields, calculates confidence scores,
and emits a single **Golden Candidate Record** as schema-valid JSON.

---

## Architecture

```
ATS JSON ──┐
           ├─► Parser Layer ─► Canonical Model ─► Normalizer ─► Merge Engine
Resume PDF ┘                                                          │
                                                                      ▼
                                             Confidence Engine ◄──────┤
                                                                      │
                                             Validation Layer  ◄──────┤
                                                                      │
                                             Projection Engine ◄──────┘
                                                                      │
                                             Golden Candidate Record  ▼
```

**Pipeline components**

| Package | Responsibility |
|---|---|
| `transformer.parsers.ats` | Parse ATS JSON into Canonical Model |
| `transformer.parsers.resume` | Extract text from PDF, parse into Canonical Model |
| `transformer.canonical` | Pydantic Canonical Candidate Model (internal representation) |
| `transformer.normalizers` | Phone → E.164, Date → ISO-8601, Country → ISO-3166, Skills |
| `transformer.merge` | Rule-based merge + conflict resolution |
| `transformer.confidence` | Rule-based field and overall confidence scoring |
| `transformer.validation` | Input / canonical / output validation |
| `transformer.projection` | Config-driven field selection and remapping |
| `transformer.pipeline` | Orchestrates all components (dependency injection) |
| `transformer.config` | Configuration loading and Pydantic validation |
| `transformer.cli` | Typer CLI entry point |

---

## Quick Start

```bash
# 1 – Install (production)
pip install -e .

# 2 – Install (development, with all dev tools)
make install-dev

# 3 – Run the transformer
transformer run \
  --ats    samples/inputs/ats_sample.json \
  --resume samples/inputs/resume_sample.pdf \
  --config config/default_output.yaml \
  --output samples/outputs/golden_record.json
```

---

## Development

```bash
make lint          # Ruff linter
make format        # Black formatter
make typecheck     # MyPy static analysis
make check         # lint + format-check + typecheck

make test          # All tests
make test-unit     # Unit tests only
make test-integration  # Integration tests only
make coverage      # Tests + HTML coverage report

make clean         # Remove cache and build artefacts
```

---

## Project Structure

```
candidate-data-transformer/
├── src/
│   └── transformer/
│       ├── cli/           # Typer CLI
│       ├── parsers/
│       │   ├── ats/       # ATS JSON parser
│       │   └── resume/    # Resume PDF parser
│       ├── canonical/     # Pydantic canonical data model
│       ├── normalizers/   # Phone, date, country, skill normalizers
│       ├── merge/         # Merge engine + conflict resolution
│       ├── confidence/    # Confidence scoring engine
│       ├── validation/    # Input / canonical / output validators
│       ├── projection/    # Output field projection + remapping
│       ├── pipeline/      # Pipeline orchestrator
│       └── config/        # Config loading + validation
├── tests/
│   ├── unit/              # Isolated unit tests per component
│   └── integration/       # End-to-end pipeline tests
├── config/
│   ├── default_output.yaml
│   └── custom_output.yaml
├── samples/
│   ├── inputs/            # Sample ATS JSON + Resume PDF
│   └── outputs/           # Generated Golden Candidate Records
├── docs/                  # Design documents
├── pyproject.toml
├── ruff.toml
├── Makefile
├── .pre-commit-config.yaml
└── .env.example
```

---

## Key Engineering Decisions

| Decision | Choice | Reason |
|---|---|---|
| Language | Python 3.12 | Ecosystem, readability, parsing libraries |
| Data Model | Pydantic v2 | Validation, serialization, type safety |
| CLI | Typer | Type-safe, minimal boilerplate |
| PDF Parsing | PyMuPDF | Fast, accurate, layout-preserving |
| Resume Strategy | Hybrid (regex + rule-based) | Deterministic + flexible |
| Merge Strategy | Source priority + field rules | Explainable, auditable |
| Confidence | Rule-based | Deterministic, interview-friendly |
| Config Format | YAML | Readable, nested structure support |
| DI Strategy | Constructor injection | Loose coupling, testable |

See `docs/` for the full Software Requirements Analysis, Research Document, and
Technology Decision Record.

---

## Canonical Schema Version

`schema_version: "1.0"` — supports ATS JSON + Resume PDF sources.
