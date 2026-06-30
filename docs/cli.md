# CLI

The installed command is `candidate-transformer`; `transformer` is retained as
an alias. Both invoke `transformer.cli:app`.

## Commands

| Command | Behavior |
| --- | --- |
| `parse FILE` | Detect ATS JSON or resume PDF/DOCX and run the single-source pipeline |
| `merge ATS RESUME` | Parse, normalize, and merge two sources |
| `validate CANDIDATE` | Validate canonical candidate JSON |
| `project CANDIDATE --format NAME` | Run one projection |
| `transform ATS RESUME` | Run the complete two-source pipeline |

## Common options

- `--output PATH`, `-o PATH`: write the JSON result to a file.
- `--debug`: print a traceback for failures.

Without `--output`, results go to stdout. Concise errors go to stderr. A failed
validation returns exit code 1 with its structured result; fatal exceptions are
mapped by the centralized CLI error handler.

Examples use files already included in the repository:

```bash
candidate-transformer parse samples/inputs/my_test.json
candidate-transformer parse samples/resumes/Standard_resume.docx -o result.json
candidate-transformer transform samples/inputs/my_test.json samples/resumes/sahil_resume.pdf
```
