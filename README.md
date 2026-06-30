# Candidate Data Transformer

Candidate Data Transformer converts ATS JSON and PDF/DOCX resumes into a
canonical candidate record. It supports normalization, deterministic merging,
confidence scoring, validation, and configurable projection.

## Requirements

- Python 3.12 or newer
- An ATS JSON file, a PDF resume, or a DOCX resume

## Installation

Install from a local checkout:

```bash
python -m pip install .
candidate-transformer --help
```

For development:

```bash
python -m pip install -e ".[dev]"
```

The legacy `transformer` command is retained as an alias for
`candidate-transformer`.

## CLI

```bash
candidate-transformer parse samples/resumes/Standard_resume.docx
candidate-transformer merge samples/inputs/my_test.json samples/resumes/sahil_resume.pdf
candidate-transformer validate candidate.json
candidate-transformer project candidate.json --format assignment
candidate-transformer transform ats.json resume.pdf --format canonical
```

Every command supports `--output PATH` and `--debug`. Without `--output`, JSON
is written to stdout. Errors are written to stderr; tracebacks are shown only
with `--debug`.

## Processing model

```text
CLI -> ApplicationService -> Pipeline -> Ordered stages
```

The application service selects the stage order for each use case. The pipeline
only executes the supplied stages and propagates `PipelineState`. Business
engines remain independently testable and constructor-injected.

## Configuration

Runtime configuration is stored in `config/`:

- `confidence_rules.yaml`
- `merge_policy.yaml`
- `projection_rules.yaml`
- `skill_aliases.yaml`
- `validation_rules.yaml`

See [docs/index.md](docs/index.md) for architecture, models, configuration,
extension guidance, and API documentation.

## Development

```bash
python -m ruff check src tests
python -m black src tests
python -m mypy src
python -m pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) before making changes.

## License

Released under the [MIT License](LICENSE).
