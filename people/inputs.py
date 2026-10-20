"""Entrada base de pessoa (ADR-0012, ADR-0016): subclasses acrescentam só os próprios campos."""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from people.domain import PHONE_LENGTHS, is_valid_cpf, only_digits
from shared.http import request_mapping
from shared.validation import to_ptbr_errors

PERSON_LABELS = {"name": "nome", "cpf": "CPF", "email": "e-mail", "phone": "telefone"}

EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
CPF_REQUIRED = "O campo CPF é obrigatório."
CPF_INVALID = "O CPF informado é inválido."
EMAIL_INVALID = "O e-mail informado é inválido."
PHONE_INVALID = "O telefone deve ter DDD e 8 ou 9 dígitos."


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


class PersonInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    name: str = Field(min_length=1, max_length=120)
    cpf: str
    email: Optional[str] = Field(default=None, max_length=254)
    phone: Optional[str] = None

    @field_validator("cpf", mode="before")
    @classmethod
    def cpf_is_required(cls, value):
        if _is_blank(value):
            raise ValueError(CPF_REQUIRED)
        return value

    @field_validator("cpf")
    @classmethod
    def cpf_is_valid(cls, value):
        digits = only_digits(value)
        if not is_valid_cpf(digits):
            raise ValueError(CPF_INVALID)
        return digits

    @field_validator("email", "phone", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return None if _is_blank(value) else value

    @field_validator("email")
    @classmethod
    def email_is_valid(cls, value):
        if value is not None and not EMAIL.fullmatch(value):
            raise ValueError(EMAIL_INVALID)
        return value

    @field_validator("phone")
    @classmethod
    def phone_is_valid(cls, value):
        if value is None:
            return None
        digits = only_digits(value)
        if len(digits) not in PHONE_LENGTHS:
            raise ValueError(PHONE_INVALID)
        return digits


def parse_person(model: type[PersonInput], data, labels: Optional[dict] = None, mapping: Optional[dict] = None):
    """Valida com `model` (PersonInput ou subclasse); devolve (entrada, None) ou (None, erros pt-BR)."""
    try:
        return model.model_validate(request_mapping(data) if mapping is None else mapping), None
    except ValidationError as exc:
        return None, to_ptbr_errors(exc, {**PERSON_LABELS, **(labels or {})})
