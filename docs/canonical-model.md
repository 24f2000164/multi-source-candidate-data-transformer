# Canonical Model

`transformer.models.Candidate` is the immutable canonical record passed between
engines.

## Candidate fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Generated internal record identifier |
| `first_name` | string | Required given name |
| `last_name` | string | Required family name |
| `external_id` | string or null | External-system identifier |
| `contact` | `ContactInfo` or null | Email, phone, location, and profile URLs |
| `experiences` | list | Work-history entries |
| `education` | list | Education entries |
| `skills` | list of strings | Deduplicated skills |
| `certifications` | list | Professional certifications |
| `languages` | list of strings | Deduplicated languages |
| `confidence` | `OverallConfidence` or null | Overall and field scores |
| `provenance` | mapping | Field origin records |
| `schema_version` | string | Canonical schema version |

Models are frozen and forbid unknown fields. Transformations return copied
models rather than mutating an existing candidate. Pydantic performs canonical
input validation and JSON-safe serialization.

`DataSource` currently identifies `ATS` and `RESUME` origins. A
`FieldProvenance` records the source, raw value, and extraction timestamp.
