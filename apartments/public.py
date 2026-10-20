"""Contrato público de apartamentos (ADR-0015): único módulo que outros apps importam."""

import uuid
from dataclasses import dataclass
from typing import Optional

from apartments import repository

__all__ = [
    "ApartmentRef",
    "list_selectable_for_owner",
    "list_by_owner",
    "count_by_owner",
    "get_many",
    "assign_owner",
    "release_owner",
]


@dataclass(frozen=True)
class ApartmentRef:
    id: uuid.UUID
    label: str
    owner_id: Optional[uuid.UUID]


def _ref(record) -> ApartmentRef:
    return ApartmentRef(id=record.id, label=repository.label(record), owner_id=record.owner_id)


def list_selectable_for_owner(tenant_id, owner_id) -> list[ApartmentRef]:
    """Apartamentos sem proprietário mais os do proprietário informado (None = só os livres)."""
    return [_ref(r) for r in repository.selectable_for_owner(tenant_id, owner_id)]


def list_by_owner(tenant_id, owner_id) -> list[ApartmentRef]:
    return [_ref(r) for r in repository.by_owner(tenant_id, owner_id)]


def count_by_owner(tenant_id) -> dict[uuid.UUID, int]:
    return repository.count_by_owner(tenant_id)


def get_many(tenant_id, apartment_ids) -> dict[uuid.UUID, ApartmentRef]:
    return {r.id: _ref(r) for r in repository.by_ids(tenant_id, apartment_ids)}


def assign_owner(tenant_id, apartment_ids, owner_id) -> int:
    """Vincula só apartamentos livres ou já do proprietário; devolve quantos foram gravados."""
    return repository.assign_owner(tenant_id, apartment_ids, owner_id)


def release_owner(tenant_id, owner_id, keep_ids=()) -> int:
    return repository.release_owner(tenant_id, owner_id, keep_ids)
