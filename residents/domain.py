"""Domínio de moradores em Python puro (ADR-0014).

`Resident` herda de `Person` os atributos gerais e as regras deles (ADR-0016) e acrescenta
só o apartamento onde mora. O CPF único por condomínio entre moradores garante que a mesma
pessoa more em um único apartamento do condomínio.
"""

import uuid
from dataclasses import dataclass

from people.domain import Person


class InvalidResidentError(ValueError):
    pass


@dataclass(frozen=True)
class Resident(Person):
    apartment_id: uuid.UUID

    ROLE_LABEL = "morador"

    def __post_init__(self):
        if self.apartment_id is None:
            raise InvalidResidentError("O apartamento de moradia é obrigatório.")
