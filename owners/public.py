"""Contrato público de proprietários (ADR-0015): único módulo que outros apps importam.

Expõe só tipos simples; nunca o CPF nem models do ORM.
"""

import uuid
from dataclasses import dataclass

from owners import repository

__all__ = ["OwnerRef", "list_owners", "get_owner", "names_by_id"]


@dataclass(frozen=True)
class OwnerRef:
    id: uuid.UUID
    name: str


def list_owners(tenant_id) -> list[OwnerRef]:
    return [OwnerRef(id=o.id, name=o.name) for o in repository.list_for_tenant(tenant_id)]


def get_owner(tenant_id, owner_id) -> OwnerRef | None:
    owner = repository.get(tenant_id, owner_id)
    return OwnerRef(id=owner.id, name=owner.name) if owner else None


def names_by_id(tenant_id, owner_ids) -> dict[uuid.UUID, str]:
    return repository.names_by_id(tenant_id, owner_ids)
