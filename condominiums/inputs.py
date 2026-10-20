from pydantic import BaseModel, ConfigDict, Field, ValidationError

from shared.http import request_mapping
from shared.validation import to_ptbr_errors

LABELS = {"name": "nome"}


class CondominiumInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    name: str = Field(min_length=1, max_length=120)


def parse_condominium(data):
    """Valida a entrada; devolve (CondominiumInput, None) ou (None, erros em pt-BR)."""
    try:
        return CondominiumInput.model_validate(request_mapping(data)), None
    except ValidationError as exc:
        return None, to_ptbr_errors(exc, LABELS)
