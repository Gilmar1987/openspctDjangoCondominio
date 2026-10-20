"""Entrada de morador: herda de PersonInput e acrescenta só o apartamento (ADR-0016)."""

import uuid

from pydantic import field_validator

from people.inputs import PersonInput, parse_person

RESIDENT_LABELS = {"apartment_id": "apartamento"}
APARTMENT_REQUIRED = "O campo apartamento é obrigatório."
APARTMENT_NOT_FOUND = "O apartamento não foi encontrado neste condomínio."


class ResidentInput(PersonInput):
    apartment_id: uuid.UUID

    @field_validator("apartment_id", mode="before")
    @classmethod
    def apartment_is_uuid(cls, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(APARTMENT_REQUIRED)
        try:
            return uuid.UUID(str(value).strip())
        except ValueError:
            raise ValueError(APARTMENT_NOT_FOUND)


def parse_resident(data):
    return parse_person(ResidentInput, data, RESIDENT_LABELS)
