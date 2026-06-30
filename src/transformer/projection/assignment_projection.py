from pathlib import Path
from typing import Any

from transformer.config.config_loader import Config, ConfigLoader
from transformer.config.loader import DEFAULT_CONFIG_DIR
from transformer.models import Candidate
from transformer.projection.exceptions import ProjectionError
from transformer.projection.projection_strategy import ProjectionStrategy

_DEFAULT_RULES_PATH = DEFAULT_CONFIG_DIR / "projection_rules.yaml"


class AssignmentProjection(ProjectionStrategy):
    """Projects a ``Candidate`` into the assignment-required JSON output schema.

    When instantiated without a ``rules_path`` the projection uses a
    code-driven mapper that produces the full assignment output contract.
    When a custom ``rules_path`` is supplied the original YAML-driven
    field-rename behaviour is preserved for backward compatibility.
    """

    def __init__(
        self,
        *,
        rules_path: Path | None = None,
        config_loader: ConfigLoader | None = None,
    ) -> None:
        """Initialise the strategy.

        Args:
            rules_path: Path to a custom ``projection_rules.yaml``.  When
                supplied the YAML-driven field-rename mode is activated.
                Omit (or pass ``None``) to use the full code-driven assignment
                schema mapper.
            config_loader: Loader used in YAML-driven mode.  A private loader
                is created if omitted.

        Raises:
            ProjectionError: In YAML-driven mode, if the rules file is missing,
                invalid, or does not declare a ``fields`` mapping.
        """
        self._yaml_rules: dict[str, str] | None = None

        if rules_path is not None:
            # Custom rules_path supplied -> YAML-driven mode
            loader = config_loader or ConfigLoader()
            config: Config = loader.load(rules_path)
            fields = config.section("fields")
            if not isinstance(fields, dict) or not fields:
                raise ProjectionError(
                    f"projection rules file must declare a non-empty 'fields' "
                    f"mapping: {rules_path}"
                )
            rules: dict[str, str] = {}
            for field_path, rule in fields.items():
                if not isinstance(rule, dict) or "output" not in rule:
                    raise ProjectionError(
                        f"projection rule for {field_path!r} must declare an "
                        f"'output' key: {rules_path}"
                    )
                rules[field_path] = rule["output"]
            self._yaml_rules = rules

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def project(self, candidate: Candidate) -> dict[str, Any]:
        """Project a candidate into the configured output schema.

        Args:
            candidate: The canonical candidate record produced by the pipeline.

        Returns:
            A JSON-safe ``dict``.  Shape depends on the mode:
            - YAML-driven mode: only the configured fields, renamed.
            - Code-driven mode: the full assignment output contract.
        """
        if self._yaml_rules is not None:
            return self._project_yaml(candidate)
        return self._project_assignment(candidate)

    # ------------------------------------------------------------------
    # YAML-driven mode (custom rules_path)
    # ------------------------------------------------------------------

    def _project_yaml(self, candidate: Candidate) -> dict[str, Any]:
        """Original field-include-and-rename projection driven by YAML rules."""
        assert self._yaml_rules is not None
        source = candidate.model_dump(mode="json")
        output: dict[str, Any] = {}
        for field_path, output_key in self._yaml_rules.items():
            found, value = _resolve_path(source, field_path)
            if found and value is not None:
                output[output_key] = value
        return output

    # ------------------------------------------------------------------
    # Code-driven mode (default assignment schema)
    # ------------------------------------------------------------------

    def _project_assignment(self, candidate: Candidate) -> dict[str, Any]:
        """Full structural mapping to the assignment output contract."""
        output: dict[str, Any] = {}

        # Identity
        output["candidate_id"] = str(candidate.id)
        output["full_name"] = f"{candidate.first_name} {candidate.last_name}".strip()

        # Contact
        contact = candidate.contact
        output["emails"] = [contact.email] if (contact and contact.email) else []
        output["phones"] = [contact.phone] if (contact and contact.phone) else []
        output["location"] = _parse_location(contact.location if contact else None)
        output["links"] = {
            "linkedin": (
                str(contact.linkedin_url) if (contact and contact.linkedin_url) else ""
            ),
            "github": (
                str(contact.github_url) if (contact and contact.github_url) else ""
            ),
        }

        # Profile metadata (reserved for future enrichment)
        output["headline"] = None
        output["years_experience"] = None

        # Skills enriched with confidence + sources
        output["skills"] = self._map_skills(candidate)

        # Experience & Education
        raw = candidate.model_dump(mode="json")
        output["experience"] = raw.get("experiences", [])
        output["education"] = raw.get("education", [])

        # Provenance: dict -> list
        output["provenance"] = self._map_provenance(candidate)

        # Overall confidence
        output["overall_confidence"] = (
            candidate.confidence.score if candidate.confidence else None
        )

        return output

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_skills(candidate: Candidate) -> list[dict[str, Any]]:
        """Build the enriched skills list expected by the assignment schema."""
        skills_confidence: float | None = None
        skills_source: str | None = None

        if candidate.provenance and "skills" in candidate.provenance:
            prov = candidate.provenance["skills"]
            skills_source = _source_name(prov.source)

        if candidate.confidence and "skills" in candidate.confidence.fields:
            field_conf = candidate.confidence.fields["skills"]
            skills_confidence = field_conf.score
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
        """Flatten provenance dict to list format expected by the schema."""
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
    """Parse a free-text location string into {city, region, country}."""
    if not location_str:
        return {"city": "", "region": "", "country": ""}
    parts = [p.strip() for p in location_str.split(",")]
    return {
        "city": parts[0] if len(parts) > 0 else "",
        "region": parts[1] if len(parts) > 1 else "",
        "country": parts[2] if len(parts) > 2 else "",
    }


def _resolve_path(data: dict[str, Any], dotted_path: str) -> tuple[bool, Any]:
    """Resolve a dot-separated path against a nested dict."""
    current: Any = data
    for segment in dotted_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return False, None
        current = current[segment]
    return True, current


def _source_name(source: Any) -> str:
    """Return a clean string name for a DataSource enum or string."""
    return source.name if hasattr(source, "name") else str(source)
