# Extension Guide

Extensions must preserve package ownership and constructor injection.

## Add a projection

1. Implement `ProjectionStrategy.project(candidate)`.
2. Add configuration only when field selection or naming is data-driven.
3. Add the strategy to the `ProjectionRegistry` mapping in the composition root.
4. Add unit and integration tests for valid, missing, and invalid data.

## Add a validation rule

1. Implement the validation rule protocol with a unique stable name.
2. Add it to `build_default_registry` in the correct rule category.
3. Return issues; do not raise for ordinary validation failures.
4. Test passing, failing, and edge inputs.

## Add a pipeline stage

1. Implement the request/state `StatePipelineStage` contract.
2. Keep the stage stateless and delegate business work to an injected engine.
3. Add it to the appropriate `ApplicationService` sequence.
4. Return a report with a stable stage name and expose non-fatal warnings there.

## Add an input format

Parser architecture is frozen. A new input format requires an approved design
covering validation, parser ownership, source provenance, routing, resource
limits, and negative tests. Do not add routing heuristics without approval.
