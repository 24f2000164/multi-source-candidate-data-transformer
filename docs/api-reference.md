# API Reference

## Application

### `ApplicationService`

- `parse(file_path) -> ApplicationResult`
- `merge(ats_path, resume_path) -> ApplicationResult`
- `validate(candidate_path) -> ApplicationResult`
- `project(candidate_path, format_name) -> ApplicationResult`
- `transform(ats_path, resume_path, format_name="canonical") -> ApplicationResult`

`ApplicationResult` contains `candidate`, `projection`, `reports`, `warnings`,
`success`, and `exit_code`.

## Pipeline

- `Pipeline.execute(request, stages, state=None) -> PipelineState`
- `PipelineRequest`: immutable user inputs and options.
- `PipelineState`: mutable stage data and reports.
- `StatePipelineStage.execute(request, state) -> report | None`

## Business engines

- `ATSParser.parse(path) -> Candidate`
- `ResumeParser.parse(path) -> Candidate`
- `NormalizationEngine.normalize(candidate) -> Candidate`
- `MergeEngine.merge(candidates) -> (Candidate, MergeReport)`
- `ConfidenceEngine.run(candidate, metadata) -> (Candidate, ConfidenceReport)`
- `ValidationEngine.run(candidate) -> ValidationReport`
- `ProjectionEngine.project(candidate, projection_type) -> (dict, ProjectionReport)`

## Models

Public canonical types are exported by `transformer.models`. Projection types
are exported by `transformer.projection`. Other packages expose their typed
exceptions and reports from their respective modules.
