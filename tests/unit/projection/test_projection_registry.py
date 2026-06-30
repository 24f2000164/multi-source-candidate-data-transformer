"""Unit tests for ``ProjectionRegistry``."""

import pytest

from transformer.projection.canonical_projection import CanonicalProjection
from transformer.projection.exceptions import UnknownProjectionTypeError
from transformer.projection.projection_registry import ProjectionRegistry


class TestProjectionRegistry:
    def test_get_returns_registered_strategy(self) -> None:
        strategy = CanonicalProjection()
        registry = ProjectionRegistry({"canonical": strategy})

        assert registry.get("canonical") is strategy

    def test_get_unknown_type_raises(self) -> None:
        registry = ProjectionRegistry({"canonical": CanonicalProjection()})

        with pytest.raises(UnknownProjectionTypeError):
            registry.get("does-not-exist")

    def test_has_no_public_register_method(self) -> None:
        registry = ProjectionRegistry({})

        assert not hasattr(registry, "register")

    def test_mutating_internal_dict_does_not_affect_registry(self) -> None:
        source = {"canonical": CanonicalProjection()}
        registry = ProjectionRegistry(source)
        source["assignment"] = CanonicalProjection()

        with pytest.raises(UnknownProjectionTypeError):
            registry.get("assignment")
