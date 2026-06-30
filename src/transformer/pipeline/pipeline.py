"""Generic, stateless pipeline stage executor."""

from transformer.pipeline.context import PipelineRequest, PipelineState
from transformer.pipeline.stage import StatePipelineStage


class Pipeline:
    """Execute caller-supplied stages in their supplied order."""

    def execute(
        self,
        request: PipelineRequest,
        stages: list[StatePipelineStage],
        state: PipelineState | None = None,
    ) -> PipelineState:
        """Run stages linearly and return the resulting mutable state."""
        current = state if state is not None else PipelineState()
        for stage in stages:
            report = stage.execute(request, current)
            if report is None:
                continue
            current.reports[stage.name] = report
            for warning in getattr(report, "warnings", ()):
                message = getattr(warning, "message", str(warning))
                current.warnings.append(str(message))
        return current
