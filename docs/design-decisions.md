# Design Decisions

## Frozen layered architecture

The CLI is a delivery adapter, `ApplicationService` owns use-case orchestration,
and `Pipeline` executes caller-supplied stages. Business engines remain in their
existing packages.

## Constructor injection

Parsers, engines, registries, and the pipeline are injected. This keeps units
replaceable in tests and avoids global mutable state.

## Immutable requests, mutable state

`PipelineRequest` represents fixed user input. `PipelineState` represents data
that changes as stages execute. This avoids pretending parser stages transform
an existing candidate.

## Configuration-driven policies

Merge policy, confidence behavior, validation limits, skill aliases, and
assignment projection fields remain in YAML. Stage order is code-owned because
it defines each application use case rather than a runtime tuning parameter.

## Version and release

The package is MIT licensed at version 1.0.0. `pyproject.toml` is the only
version source. The project provides local packaging and console scripts but no
PyPI publication or release workflow.

## Deterministic failure handling

Business exceptions propagate to the CLI boundary. The CLI emits concise stderr
messages by default and tracebacks only with explicit `--debug`.
