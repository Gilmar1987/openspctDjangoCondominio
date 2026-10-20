"""Persistência de apartamentos: toda consulta parte de for_tenant() (ADR-0007, ADR-0013)."""

from contextlib import contextmanager

from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q

from apartments.domain import Apartment, DuplicateApartmentError
from apartments.models import UNIQUE_CONSTRAINT, ApartmentRecord, key_expressions

ORDERING = (
    F("tower").asc(nulls_first=True),
    F("block").asc(nulls_first=True),
    F("floor").asc(nulls_first=True),
    F("number").asc(),
)


def _to_entity(record) -> Apartment:
    return Apartment(
        id=record.id,
        tenant_id=record.tenant_id,
        tower=record.tower,
        block=record.block,
        floor=record.floor,
        number=record.number,
        owner_id=record.owner_id,
    )


def _fields(apartment: Apartment) -> dict:
    return {
        "tower": apartment.tower,
        "block": apartment.block,
        "floor": apartment.floor,
        "number": apartment.number,
        "owner_id": apartment.owner_id,
    }


@contextmanager
def _unique_violation_as_duplicate():
    """Converte a violação da constraint de unicidade (ex.: corrida) em erro de domínio."""
    try:
        with transaction.atomic():
            yield
    except IntegrityError as exc:
        if UNIQUE_CONSTRAINT in str(exc):
            raise DuplicateApartmentError() from exc
        raise


def _scoped(tenant_id):
    return ApartmentRecord.objects.for_tenant(tenant_id)


def add(apartment: Apartment) -> Apartment:
    with _unique_violation_as_duplicate():
        record = ApartmentRecord.objects.create(tenant_id=apartment.tenant_id, **_fields(apartment))
    return _to_entity(record)


def update(apartment: Apartment) -> Apartment | None:
    with _unique_violation_as_duplicate():
        updated = _scoped(apartment.tenant_id).filter(id=apartment.id).update(**_fields(apartment))
    return apartment if updated else None


def get(tenant_id, apartment_id) -> Apartment | None:
    record = _scoped(tenant_id).filter(id=apartment_id).first()
    return _to_entity(record) if record else None


def list_for_tenant(tenant_id) -> list[Apartment]:
    return [_to_entity(r) for r in _scoped(tenant_id).order_by(*ORDERING)]


def find_same_key(apartment: Apartment) -> list[Apartment]:
    tower, block, number = apartment.natural_key
    matches = (
        _scoped(apartment.tenant_id)
        .annotate(**key_expressions())
        .filter(key_tower=tower, key_block=block, key_number=number)
    )
    return [_to_entity(r) for r in matches]


def delete(tenant_id, apartment_id) -> bool:
    deleted, _ = _scoped(tenant_id).filter(id=apartment_id).delete()
    return deleted > 0


# Vínculo com proprietários (usado por apartments.public, ADR-0015)


def label(record) -> str:
    parts = []
    if record.tower:
        parts.append(f"Torre {record.tower}")
    if record.block:
        parts.append(f"Bloco {record.block}")
    parts.append(f"Nº {record.number}")
    return " · ".join(parts)


def selectable_for_owner(tenant_id, owner_id) -> list:
    free = Q(owner_id__isnull=True)
    if owner_id is not None:
        free |= Q(owner_id=owner_id)
    return list(_scoped(tenant_id).filter(free).order_by(*ORDERING))


def by_owner(tenant_id, owner_id) -> list:
    return list(_scoped(tenant_id).filter(owner_id=owner_id).order_by(*ORDERING))


def by_ids(tenant_id, apartment_ids) -> list:
    return list(_scoped(tenant_id).filter(id__in=list(apartment_ids)))


def count_by_owner(tenant_id) -> dict:
    rows = (
        _scoped(tenant_id)
        .filter(owner_id__isnull=False)
        .values("owner_id")
        .annotate(total=Count("id"))
    )
    return {row["owner_id"]: row["total"] for row in rows}


def assign_owner(tenant_id, apartment_ids, owner_id) -> int:
    """UPDATE condicional: nunca toma um apartamento que já tem outro proprietário."""
    return (
        _scoped(tenant_id)
        .filter(id__in=list(apartment_ids))
        .filter(Q(owner_id__isnull=True) | Q(owner_id=owner_id))
        .update(owner_id=owner_id)
    )


def release_owner(tenant_id, owner_id, keep_ids=()) -> int:
    return (
        _scoped(tenant_id)
        .filter(owner_id=owner_id)
        .exclude(id__in=list(keep_ids))
        .update(owner_id=None)
    )
