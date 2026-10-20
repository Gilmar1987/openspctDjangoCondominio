"""Persistência de apartamentos: toda consulta parte de for_tenant() (ADR-0007, ADR-0013)."""

from contextlib import contextmanager

from django.db import IntegrityError, transaction
from django.db.models import F

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
    )


def _fields(apartment: Apartment) -> dict:
    return {
        "tower": apartment.tower,
        "block": apartment.block,
        "floor": apartment.floor,
        "number": apartment.number,
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
