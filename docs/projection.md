# Projection

Projection converts a canonical `Candidate` into a JSON-safe dictionary without
mutating the candidate.

## Implemented projections

- `canonical`: emits the full canonical model using Pydantic JSON mode.
- `assignment`: emits configured fields and output names from
  `config/projection_rules.yaml`; absent optional values are omitted.

`ProjectionRegistry` is immutable after construction. `ProjectionEngine`
resolves the requested strategy, returns the output dictionary, and returns a
`ProjectionReport` containing the projection name, field count, and warnings.
An unknown name raises `UnknownProjectionTypeError`.

Use the CLI with:

```bash
candidate-transformer project candidate.json --format assignment
candidate-transformer transform ats.json resume.pdf --format canonical
```
