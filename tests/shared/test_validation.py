from typing import Optional

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from shared.validation import to_ptbr_errors

LABELS = {"name": "nome", "code": "código", "size": "tamanho"}


class Sample(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=5)
    code: Optional[str] = None
    size: Optional[int] = None

    @field_validator("code")
    @classmethod
    def code_must_not_be_x(cls, value):
        if value == "x":
            raise ValueError("O código não pode ser x.")
        return value


def errors_for(data):
    with pytest.raises(ValidationError) as exc:
        Sample.model_validate(data)
    return to_ptbr_errors(exc.value, LABELS)


def test_missing_field_is_required():
    assert errors_for({}) == {"name": ["O campo nome é obrigatório."]}


def test_blank_string_is_required():
    assert errors_for({"name": "   "}) == {"name": ["O campo nome é obrigatório."]}


def test_string_too_long_reports_limit():
    assert errors_for({"name": "abcdef"}) == {
        "name": ["O campo nome deve ter no máximo 5 caracteres."]
    }


def test_wrong_type_for_text():
    assert errors_for({"name": 10}) == {"name": ["O campo nome deve ser um texto."]}


def test_integer_parsing_error():
    assert errors_for({"name": "ok", "size": "grande"}) == {
        "size": ["O campo tamanho deve ser um número inteiro."]
    }


def test_value_error_uses_validator_message():
    assert errors_for({"name": "ok", "code": "x"}) == {"code": ["O código não pode ser x."]}


def test_unknown_field_uses_field_name_as_label():
    class Other(BaseModel):
        other: int

    with pytest.raises(ValidationError) as exc:
        Other.model_validate({})
    assert to_ptbr_errors(exc.value, {}) == {"other": ["O campo other é obrigatório."]}


def test_unmapped_error_type_falls_back_to_invalid():
    class Flag(BaseModel):
        flag: bool

    with pytest.raises(ValidationError) as exc:
        Flag.model_validate({"flag": "talvez"})
    assert to_ptbr_errors(exc.value, {"flag": "indicador"}) == {
        "flag": ["O campo indicador é inválido."]
    }


def test_multiple_errors_are_grouped_by_field():
    errors = errors_for({"name": "abcdef", "size": "x"})

    assert set(errors) == {"name", "size"}
