"""``AssignmentProjection``: maps a ``Candidate`` to the assignment JSON schema.

The YAML-driven field-rename approach used in the previous implementation
cannot express the structural transformations required by the assignment
output contract (list wrapping, object decomposition, field combination,
provenance flattening, skills enrichment). This module replaces that
approach with explicit mapping logic while preserving the same public
interface so the CLI composition root requires no changes.

Mapping summary
---------------
Internal field                   → Assignment output key
--------------------------------   --------------------------
id                               → candidate_id
first_name + last_name           → full_name
contact.email                    → emails[]
contact.phone                    → phones[]
contact.location (free-text)     → location {city, region, country}
contact.linkedin_url             → links.linkedin
contact.github_url               → links.github
experiences                      → experience
confidence.score                 → overall_confidence
skills (list[str])               → skills [{name, confidence, sources}]
provenance (dict)                → provenance [{field, source, method}]
"""

from pathlib import Path
from typing import Any

from transformer.models import Candidate
from transformer.projection.projection_strategy import ProjectionStrategy


class AssignmentProjection(ProjectionStrategy):
    """Projects a ``Candidate`` into the assignment-required JSON output schema.

    Transforms the rich internal domain model into the flat canonical schema
    expected by the assignment evaluator. The internal ``Candidate`` model is
    never modified; only the serialised output representation changes.

    The constructor accepts (and silently ignores) the legacy ``config_loader``
    and ``rules_path`` keyword arguments so that the existing CLI composition
    root (``cli/app.py``) continues to work without modification.
    """

    def __init__(
        self,
        *,
        rules_path: Path | None = None,  # accepted for backward-compat, unused
        config_loader: Any = None,       # accepted for backward-compat, unused
    ) -> None:
        """Initialise the projection strategy.

        Args:
            rules_path: Ignored. Retained for backward compatibility.
            config_loader: Ignored. Retained for backward compatibility.
        """

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def project(self, candidate: Candidate) -> dict[str, Any]:
        """Map a ``Candidate`` to the assignment output schema.

        Args:
            candidate: The canonical candidate record produced by the pipeline.

        Returns:
            A JSON-safe ``dict`` matching the assignment default output schema.
        """
        output: dict[str, Any] = {}

        # ── Identity ──────────────────────────────────────────────────────────
        output["candidate_id"] = str(candidate.id)
        output["full_name"] = (
            f"{candidate.first_name} {candidate.last_name}".strip()
        )

        # ── Contact ───────────────────────────────────────────────────────────
        contact = candidate.contact
        output["emails"] = [contact.email] if (contact and contact.email) else []
        output["phones"] = [contact.phone] if (contact and contact.phone) else []
        output["location"] = _parse_location(
            contact.location if contact else None
        )
        output["links"] = {
            "linkedin": (
                str(contact.linkedin_url)
                if (contact and contact.linkedin_url)
                else ""
            ),
            "github": (
                str(contact.github_url)
                if (contact and contact.github_url)
                else ""
            ),
        }

        # ── Profile metadata (reserved for future enrichment) ─────────────────
        output["headline"] = None
        output["years_experience"] = None

        # ── Skills with confidence + sources ─────────────────────────────────
        # The internal model stores per-field (not per-skill-item) confidence.
        # We resolve a single confidence score + source for the "skills" field
        # and apply it uniformly across every skill tag.
        output["skills"] = self._map_skills(candidate)

        # ── Experience & Education ────────────────────────────────────────────
        raw = candidate.model_dump(mode="json")
        output["experience"] = raw.get("experiences", [])
        output["education"] = raw.get("education", [])

        # ── Provenance  dict[field, FieldProvenance] → list[{field, source, method}]
        output["provenance"] = self._map_provenance(candidate)

        # ── Overall confidence ────────────────────────────────────────────────
        output["overall_confidence"] = (
            candidate.confidence.score if candidate.confidence else None
        )

        return output

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_skills(candidate: Candidate) -> list[dict[str, Any]]:
        """Build the enriched skills list expected by the assignment schema.

        Each skill tag is wrapped with the confidence score and source list
        derived from the pipeline's per-field confidence and provenance data.
        """
        skills_confidence: float | None = None
        skills_source: str | None = None

        # Prefer provenance as the authoritative source attribution
        if candidate.provenance and "skills" in candidate.provenance:
            prov = candidate.provenance["skills"]
            skills_source = _source_name(prov.source)

        # Confidence score comes from the per-field confidence map
        if candidate.confidence and "skills" in candidate.confidence.fields:
            field_conf = candidate.confidence.fields["skills"]
            skills_confidence = field_conf.score
            # Fall back to confidence source if provenance was absent
            if skills_source is None:
                skills_source = _source_name(field_conf.source)

        return [
            {
                "name": skill,
                "confidence": (
                    round(skills_confidence, 4)
                    if skills_confidence is not None
                    else None
                ),
                "sources": [skills_source] if skills_source else [],
            }
            for skill in candidate.skills
        ]

    @staticmethod
    def _map_provenance(candidate: Candidate) -> list[dict[str, str]]:
        """Flatten the provenance dict into the list format expected by the schema.

        Internal shape:  ``{field_name: FieldProvenance}``
        Output shape:    ``[{field, source, method}]``
        """
        return [
            {
                "field": field_name,
                "source": _source_name(prov.source),
                "method": "Extracted",
            }
            for field_name, prov in candidate.provenance.items()
        ]


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _parse_location(location_str: str | None) -> dict[str, str]:
    """Parse a free-text location string into a structured object.

    The internal model stores location as a free-text string, e.g.
    ``"Dehradun, Uttarakhand, India"``. This function splits on commas and
    maps the parts to ``city``, ``region``, and ``country``. Missing parts
    default to an empty string.

    Args:
        location_str: Free-text location or ``None``.

    Returns:
        A dict with keys ``city``, ``region``, and ``country``.
    """
    if not location_str:
        return {"city": "", "region": "", "country": ""}
    parts = [p.strip() for p in location_str.split(",")]
    return {
        "city": parts[0] if len(parts) > 0 else "",
        "region": parts[1] if len(parts) > 1 else "",
        "country": parts[2] if len(parts) > 2 else "",
    }


def _source_name(source: Any) -> str:
    """Return a clean string name for a ``DataSource`` enum value or string.

    Args:
        source: A ``DataSource`` enum instance or any object.

    Returns:
        The ``.name`` attribute when available, otherwise ``str(source)``.
    """
    return source.name if hasattr(source, "name") else str(source)