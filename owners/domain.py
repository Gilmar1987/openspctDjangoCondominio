"""Domínio de proprietários em Python puro (ADR-0014).

`Owner` herda de `Person` os atributos gerais e as regras deles (ADR-0016); aqui ficam só
as regras próprias do proprietário: o vínculo 1:N com apartamentos.
"""

import uuid
from dataclasses import dataclass
from typing import Iterable, Optional

from people.domain import Person


class ApartmentNotFoundError(Exception):
    def __init__(self):
        super().__init__("O apartamento não foi encontrado neste condomínio.")


class ApartmentTakenError(Exception):
    def __init__(self, label: str):
        super().__init__(f"O apartamento {label} já tem outro proprietário.")


@dataclass(frozen=True)
class Owner(Person):
    ROLE_LABEL = "proprietário"


def plan_apartment_links(
    owner_id: Optional[uuid.UUID],
    requested_ids: Iterable[uuid.UUID],
    found: dict[uuid.UUID, tuple[str, Optional[uuid.UUID]]],
    currently_owned: set[uuid.UUID],
) -> tuple[set[uuid.UUID], set[uuid.UUID]]:
    """Calcula o vínculo pedido para o proprietário.

    `found` traz, para cada apartamento do condomínio encontrado, (rótulo, dono atual).
    Devolve (a vincular, a liberar). Só aceita apartamentos livres ou já do proprietário.
    """
    requested = set(requested_ids)
    for apartment_id in requested:
        if apartment_id not in found:
            raise ApartmentNotFoundError()
        label, current_owner = found[apartment_id]
        if current_owner is not None and current_owner != owner_id:
            raise ApartmentTakenError(label)
    return requested - currently_owned, currently_owned - requested
