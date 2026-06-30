"""Unit tests for transformer.parsers.schema_validator."""

from typing import Any

import pytest

from transformer.parsers.exceptions import SchemaValidationError
from transformer.parsers.schema_validator import SchemaValidator


@pytest.fixture
def validator() -> SchemaValidator:
    return SchemaValidator()


def _minimal_valid() -> dict[str, Any]:
    return {"first_name": "Alice", "last_name": "Smith"}


@pytest.mark.unit
class TestSchemaValidatorHappyPath:
    def test_minimal_valid_record_passes(self, validator: SchemaValidator) -> None:
        result = validator.validate(_minimal_valid())
        assert result.unknown_fields == ()

    def test_full_valid_record_passes(self, validator: SchemaValidator) -> None:
        data = {
            **_minimal_valid(),
            "candidate_id": "ATS-1001",
            "email": "alice@example.com",
            "phone": "1234567890",
            "skills": ["Python", "FastAPI"],
            "experience": [{"company": "Acme", "title": "Engineer"}],
            "education": [{"institution": "MIT", "degree": "BS"}],
            "certifications": [{"name": "AWS Certified"}],
            "languages": ["English"],
        }
        result = validator.validate(data)
        assert result.unknown_fields == ()


@pytest.mark.unit
class TestSchemaValidatorRootType:
    def test_non_dict_root_raises(self, validator: SchemaValidator) -> None:
        with pytest.raises(SchemaValidationError, match="must be an object"):
            validator.validate([])  # type: ignore[arg-type]

    def test_string_root_raises(self, validator: SchemaValidator) -> None:
        with pytest.raises(SchemaValidationError, match="must be an object"):
            validator.validate("not a dict")  # type: ignore[arg-type]


@pytest.mark.unit
class TestSchemaValidatorRequiredFields:
    def test_missing_first_name_raises(self, validator: SchemaValidator) -> None:
        data = _minimal_valid()
        del data["first_name"]
        with pytest.raises(SchemaValidationError, match="first_name"):
            validator.validate(data)

    def test_missing_last_name_raises(self, validator: SchemaValidator) -> None:
        data = _minimal_valid()
        del data["last_name"]
        with pytest.raises(SchemaValidationError, match="last_name"):
            validator.validate(data)

    def test_null_first_name_raises(self, validator: SchemaValidator) -> None:
        data = {**_minimal_valid(), "first_name": None}
        with pytest.raises(SchemaValidationError, match="null"):
            validator.validate(data)

    def test_blank_first_name_raises(self, validator: SchemaValidator) -> None:
        data = {**_minimal_valid(), "first_name": "   "}
        with pytest.raises(SchemaValidationError, match="blank"):
            validator.validate(data)

    def test_non_string_first_name_raises(self, validator: SchemaValidator) -> None:
        data = {**_minimal_valid(), "first_name": 123}
        with pytest.raises(SchemaValidationError, match="must be a string"):
            validator.validate(data)

    def test_oversized_string_raises(self, validator: SchemaValidator) -> None:
        data = {**_minimal_valid(), "first_name": "x" * 10_001}
        with pytest.raises(SchemaValidationError, match="maximum length"):
            validator.validate(data)


@pytest.mark.unit
class TestSchemaValidatorListFields:
    def test_skills_not_a_list_raises(self, validator: SchemaValidator) -> None:
        data = {**_minimal_valid(), "skills": "Python"}
        with pytest.raises(SchemaValidationError, match="must be an array"):
            validator.validate(data)

    def test_skills_with_non_string_item_raises(
        self, validator: SchemaValidator
    ) -> None:
        data = {**_minimal_valid(), "skills": ["Python", 123]}
        with pytest.raises(SchemaValidationError, match="must contain only strings"):
            validator.validate(data)

    def test_experience_not_a_list_raises(self, validator: SchemaValidator) -> None:
        data = {**_minimal_valid(), "experience": {"company": "Acme"}}
        with pytest.raises(SchemaValidationError, match="must be an array"):
            validator.validate(data)

    def test_experience_with_non_object_item_raises(
        self, validator: SchemaValidator
    ) -> None:
        data = {**_minimal_valid(), "experience": ["not an object"]}
        with pytest.raises(SchemaValidationError, match="must contain only objects"):
            validator.validate(data)

    def test_null_list_field_is_allowed(self, validator: SchemaValidator) -> None:
        data = {**_minimal_valid(), "skills": None}
        result = validator.validate(data)
        assert result.unknown_fields == ()

    def test_empty_list_fields_pass(self, validator: SchemaValidator) -> None:
        data = {
            **_minimal_valid(),
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "languages": [],
        }
        result = validator.validate(data)
        assert result.unknown_fields == ()


@pytest.mark.unit
class TestSchemaValidatorUnknownFields:
    def test_unknown_top_level_field_does_not_raise(
        self, validator: SchemaValidator
    ) -> None:
        data = {**_minimal_valid(), "favorite_color": "blue"}
        result = validator.validate(data)
        assert result.unknown_fields == ("favorite_color",)

    def test_multiple_unknown_fields_collected(
        self, validator: SchemaValidator
    ) -> None:
        data = {**_minimal_valid(), "foo": 1, "bar": 2}
        result = validator.validate(data)
        assert set(result.unknown_fields) == {"foo", "bar"}

    def test_deeply_nested_unknown_object_does_not_raise(
        self, validator: SchemaValidator
    ) -> None:
        data = {**_minimal_valid(), "nested_junk": {"a": {"b": {"c": {"d": 1}}}}}
        result = validator.validate(data)
        assert result.unknown_fields == ("nested_junk",)
