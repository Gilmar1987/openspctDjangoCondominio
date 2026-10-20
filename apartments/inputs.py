import re
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from shared.http import request_mapping
from shared.validation import to_ptbr_errors

LABELS = {"number": "número", "tower": "torre", "block": "bloco", "floor": "andar", "owner_id": "proprietário"}
OWNER_NOT_FOUND = "O proprietário não foi encontrado neste condomínio."

FLOOR_MIN, FLOOR_MAX = -5, 200
FLOOR_MESSAGE = f"O andar deve ser um número inteiro entre {FLOOR_MIN} e {FLOOR_MAX}."
NUMBER_REQUIRED = "O campo número é obrigatório."
INTEGER = re.compile(r"-?\d+")


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


class ApartmentInput(BaseModel):
    """Entrada de criação e edição; campos extras (ex.: tenant) são descartados."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    number: str = Field(max_length=10)
    tower: Optional[str] = Field(default=None, max_length=20)
    block: Optional[str] = Field(default=None, max_length=20)
    floor: Optional[int] = None
    owner_id: Optional[uuid.UUID] = None

    @field_validator("owner_id", mode="before")
    @classmethod
    def owner_is_uuid(cls, value):
        if _is_blank(value):
            return None
        try:
            return uuid.UUID(str(value))
        except ValueError:
            raise ValueError(OWNER_NOT_FOUND)

    @field_validator("number", mode="before")
    @classmethod
    def number_is_required(cls, value):
        if _is_blank(value):
            raise ValueError(NUMBER_REQUIRED)
        return value

    @field_validator("tower", "block", mode="before")
    @classmethod
    def blank_text_is_absent(cls, value):
        return None if _is_blank(value) else value

    @field_validator("floor", mode="before")
    @classmethod
    def floor_in_range(cls, value):
        if _is_blank(value):
            return None
        if isinstance(value, bool):
            raise ValueError(FLOOR_MESSAGE)
        if isinstance(value, int):
            floor = value
        elif isinstance(value, str) and INTEGER.fullmatch(value.strip()):
            floor = int(value.strip())
        else:
            raise ValueError(FLOOR_MESSAGE)
        if not FLOOR_MIN <= floor <= FLOOR_MAX:
            raise ValueError(FLOOR_MESSAGE)
        return floor


def parse_apartment(data):
    """Valida a entrada; devolve (ApartmentInput, None) ou (None, erros em pt-BR)."""
    try:
        return ApartmentInput.model_validate(request_mapping(data)), None
    except ValidationError as exc:
        return None, to_ptbr_errors(exc, LABELS)
