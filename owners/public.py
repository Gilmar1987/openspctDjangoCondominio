"""Contrato público de proprietários (ADR-0015): único módulo que outros apps importam.

Expõe só tipos simples e nunca models do ORM. O CPF só sai por `get_owner_person`, usado no
pré-preenchimento explícito de formulário (exceção prevista na ADR-0017).
"""

import uuid
from dataclasses import dataclass
from typing import Optional

from owners import repository

__all__ = [
    "OwnerRef",
    "OwnerPerson",
    "list_owners",
    "get_owner",
    "names_by_id",
    "owners_by_cpf_hash",
    "get_owner_person",
]


@dataclass(frozen=True)
class OwnerRef:
    id: uuid.UUID
    name: str


@dataclass(frozen=True)
class OwnerPerson:
    name: str
    cpf: str
    email: Optional[str]
    phone: Optional[str]


def owners_by_cpf_hash(tenant_id, hashes) -> dict[str, OwnerRef]:
    """hash do CPF -> proprietário com esse CPF no mesmo condomínio (ADR-0017)."""
    hashes = list(hashes)
    if not hashes:
        return {}
    return {h: OwnerRef(id=i, name=n) for h, i, n in repository.by_cpf_hashes(tenant_id, hashes)}


def get_owner_person(tenant_id, owner_id) -> OwnerPerson | None:
    owner = repository.get(tenant_id, owner_id)
    if owner is None:
        return None
    return OwnerPerson(name=owner.name, cpf=owner.cpf, email=owner.email, phone=owner.phone)


def list_owners(tenant_id) -> list[OwnerRef]:
    return [OwnerRef(id=o.id, name=o.name) for o in repository.list_for_tenant(tenant_id)]


def get_owner(tenant_id, owner_id) -> OwnerRef | None:
    owner = repository.get(tenant_id, owner_id)
    return OwnerRef(id=owner.id, name=owner.name) if owner else None


def names_by_id(tenant_id, owner_ids) -> dict[uuid.UUID, str]:
    return repository.names_by_id(tenant_id, owner_ids)
