"""Request and mutable state objects used by pipeline orchestration."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from transformer.confidence.merge_metadata import MergeMetadata
from transformer.models import Candidate


@dataclass(frozen=True)
class PipelineRequest:
    """Immutable inputs and options for one pipeline execution."""

    ats_path: Path | None = None
    resume_path: Path | None = None
    candidate_path: Path | None = None
    projection_format: str | None = None
    output_path: Path | None = None


@dataclass
class PipelineState:
    """Mutable data propagated through an ordered stage sequence."""

    ats_candidate: Candidate | None = None
    resume_candidate: Candidate | None = None
    merged_candidate: Candidate | None = None
    merge_metadata: MergeMetadata | None = None
    projection: dict[str, Any] | None = None
    reports: dict[str, object] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def require_candidate(self) -> Candidate:
        """Return the current candidate or fail if no prior stage produced one."""
        if self.merged_candidate is None:
            raise RuntimeError("pipeline stage requires a candidate")
        return self.merged_candidate
