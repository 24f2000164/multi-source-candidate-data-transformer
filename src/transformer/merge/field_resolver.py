"""FieldResolver: given N provenance-tagged values for one canonical field,
picks the winner by dispatching to the appropriate ``BaseResolver`` subclass
per the configured ``MergePolicy``.
"""

from transformer.merge.policy import MergePolicy
from transformer.merge.resolvers import (
    BaseResolver,
    CertificationResolver,
    EducationResolver,
    ExperienceResolver,
    ListResolver,
    ResolutionResult,
    StringResolver,
)
from transformer.merge.strategies import SourceValue

_FLAT_LIST_FIELDS = frozenset({"skills", "languages"})
_STRUCTURED_LIST_RESOLVERS: dict[str, BaseResolver] = {
    "experiences": ExperienceResolver(),
    "education": EducationResolver(),
    "certifications": CertificationResolver(),
}


class FieldResolver:
    """Resolves a single canonical field's value across N sources.

    Dispatch is determined purely by field *kind* (scalar / flat list /
    structured list), never by field *name* baked into conditionals -- new
    fields only require an entry in the dispatch tables above plus a
    ``MergePolicy`` rule, not a code change to this class.
    """

    def __init__(self, policy: MergePolicy) -> None:
        """Initialise with the merge policy to consult for each field.

        Args:
            policy: The loaded ``MergePolicy``.
        """
        self._policy = policy
        self._string_resolver = StringResolver()
        self._list_resolver = ListResolver()

    def resolve(self, field_name: str, values: list[SourceValue]) -> ResolutionResult:
        """Resolve one canonical field.

        Args:
            field_name: Canonical (dotted) field name.
            values: One ``SourceValue`` per source that attempted to supply
                this field.

        Returns:
            The resolution outcome.
        """
        rule = self._policy.rule_for(field_name)
        resolver = self._resolver_for(field_name)
        return resolver.resolve(field_name, values, rule)

    def _resolver_for(self, field_name: str) -> BaseResolver:
        if field_name in _STRUCTURED_LIST_RESOLVERS:
            return _STRUCTURED_LIST_RESOLVERS[field_name]
        if field_name in _FLAT_LIST_FIELDS:
            return self._list_resolver
        return self._string_resolver
