"""``AssignmentProjection``: maps a ``Candidate`` to the assignment JSON shape.

Field inclusion and renaming are declared in ``config/projection_rules.yaml``
(loaded once at construction time via the shared ``ConfigLoader``). No
transform expressions or DSLs are supported -- only inclusion and renaming,
per the Sprint 08 design.
"""

from pathlib import Path
from typing import Any

from transformer.config.config_loader import Config, ConfigLoader
from transformer.config.loader import DEFAULT_CONFIG_DIR
from transformer.models import Candidate
from transformer.projection.exceptions import ProjectionError
from transformer.projection.projection_strategy import ProjectionStrategy

_DEFAULT_RULES_PATH = DEFAULT_CONFIG_DIR / "projection_rules.yaml"


class AssignmentProjection(ProjectionStrategy):
    """Projects a candidate into the assignment-required JSON structure.

    Field selection and renaming are driven entirely by
    ``projection_rules.yaml`` so that adding or renaming an output field
    never requires a code change.
    """

    def __init__(
        self,
        *,
        rules_path: Path = _DEFAULT_RULES_PATH,
        config_loader: ConfigLoader | None = None,
    ) -> None:
        """Initialise the strategy and eagerly load its field rules.

        Args:
            rules_path: Path to the ``projection_rules.yaml`` file.
            config_loader: Loader used to read and validate the rules file.
                A private loader is created if omitted.

        Raises:
            ProjectionError: If the rules file is missing, invalid, or does
                not declare a ``fields`` mapping.
        """
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
        self._rules: dict[str, str] = rules

    def project(self, candidate: Candidate) -> dict[str, Any]:
        """Project a candidate into the assignment JSON structure.

        Args:
            candidate: The canonical candidate record to project.

        Returns:
            A JSON-safe dict containing only the configured fields, renamed
            to their configured output keys. Canonical fields that are
            absent (e.g. an unset optional field) are omitted from the
            output rather than included as ``null``.
        """
        source = candidate.model_dump(mode="json")
        output: dict[str, Any] = {}
        for field_path, output_key in self._rules.items():
            found, value = _resolve_path(source, field_path)
            if found and value is not None:
                output[output_key] = value
        return output


def _resolve_path(data: dict[str, Any], dotted_path: str) -> tuple[bool, Any]:
    """Resolve a dot-separated path against a nested dict.

    Args:
        data: The dict to navigate.
        dotted_path: A dot-separated field path, e.g. ``"contact.email"``.

    Returns:
        A ``(found, value)`` tuple. ``found`` is ``False`` if any segment of
        the path is absent or not a dict.
    """
    current: Any = data
    for segment in dotted_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return False, None
        current = current[segment]
    return True, current
