"""Unit tests for ``CanonicalProjection``."""

import json

from tests.unit.projection._builders import full_candidate, make_candidate
from transformer.projection.canonical_projection import CanonicalProjection


class TestCanonicalProjection:
    def test_returns_all_top_level_fields(self) -> None:
        candidate = full_candidate()
        result = CanonicalProjection().project(candidate)

        assert set(result.keys()) == set(candidate.model_dump(mode="json").keys())

    def test_uuid_and_date_are_json_safe(self) -> None:
        candidate = full_candidate()
        result = CanonicalProjection().project(candidate)

        assert isinstance(result["id"], str)
        assert result["experiences"][0]["start_date"] == "2020-01-01"
        assert json.dumps(result)  # raises if not JSON-serializable

    def test_does_not_mutate_candidate(self) -> None:
        candidate = full_candidate()
        before = candidate.model_dump(mode="json")
        CanonicalProjection().project(candidate)

        assert candidate.model_dump(mode="json") == before

    def test_minimal_candidate(self) -> None:
        candidate = make_candidate(external_id=None)
        result = CanonicalProjection().project(candidate)

        assert result["first_name"] == "Jane"
        assert result["contact"] is None
        assert result["experiences"] == []

    def test_unicode_fields_preserved(self) -> None:
        candidate = make_candidate(first_name="José", last_name="Müller")
        result = CanonicalProjection().project(candidate)

        assert result["first_name"] == "José"
        assert result["last_name"] == "Müller"
