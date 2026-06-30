# Configuration

Configuration is YAML stored in the repository-level `config/` directory.
Files with schema versions are loaded by `ConfigLoader`, which validates the
supported version and caches values for one loader instance.

| File | Consumer |
| --- | --- |
| `confidence_rules.yaml` | Confidence strategies, source weights, field weights, and scored fields |
| `merge_policy.yaml` | Merge strategies, source priority, and identity keys |
| `projection_rules.yaml` | Assignment projection field inclusion and output names |
| `skill_aliases.yaml` | Skill alias normalization |
| `validation_rules.yaml` | Validation limits and phone-region defaults |
| `default_output.yaml` | Existing output configuration sample |
| `custom_output.yaml` | Existing custom output configuration sample |

Invalid, missing, or unsupported configuration fails with a typed exception.
Thresholds, field mappings, and merge priority should be changed in YAML rather
than hardcoded in engines.

Do not add `pipeline.yaml` unless a genuine runtime option is introduced. The
current stage order is selected by `ApplicationService`, not configuration.
