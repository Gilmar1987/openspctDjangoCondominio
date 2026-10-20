"""Entrada de proprietário: herda de PersonInput e acrescenta só os apartamentos (ADR-0016)."""

import uuid

from pydantic import Field, field_validator

from people.inputs import PersonInput, parse_person
from shared.http import request_mapping

OWNER_LABELS = {"apartment_ids": "apartamentos"}
APARTMENT_INVALID = "Apartamento inválido."


class OwnerInput(PersonInput):
    apartment_ids: list[uuid.UUID] = Field(default_factory=list)

    @field_validator("apartment_ids", mode="before")
    @classmethod
    def apartment_ids_are_uuids(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError(APARTMENT_INVALID)
        unique = []
        for item in value:
            try:
                apartment_id = uuid.UUID(str(item)) if isinstance(item, (str, uuid.UUID)) else None
            except ValueError:
                apartment_id = None
            if apartment_id is None:
                raise ValueError(APARTMENT_INVALID)
            if apartment_id not in unique:
                unique.append(apartment_id)
        return unique


def parse_owner(data):
    """Aceita JSON (lista) ou formulário (`apartment_ids` repetido via getlist)."""
    mapping = request_mapping(data)
    if hasattr(data, "getlist"):
        mapping["apartment_ids"] = [value for value in data.getlist("apartment_ids") if value]
    return parse_person(OwnerInput, data, OWNER_LABELS, mapping)
