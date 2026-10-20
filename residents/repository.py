"""Persistência de moradores: toda consulta parte de for_tenant() (ADR-0007, ADR-0013)."""

from contextlib import contextmanager

from django.db import IntegrityError, transaction
from django.db.models import Count
from django.db.models.functions import Lower

from people.domain import DuplicateCpfError
from residents.domain import Resident
from residents.models import ResidentRecord

ORDERING = (Lower("name"), "name")


def _to_entity(record) -> Resident:
    return Resident(
        id=record.id,
        tenant_id=record.tenant_id,
        name=record.name,
        cpf=record.get_cpf(),
        email=record.email,
        phone=record.phone,
        apartment_id=record.apartment_id,
    )


def _apply(record, resident: Resident) -> None:
    record.name = resident.name
    record.email = resident.email
    record.phone = resident.phone
    record.apartment_id = resident.apartment_id
    record.set_cpf(resident.cpf)


@contextmanager
def _cpf_violation_as_duplicate():
    """Converte a violação da unicidade de CPF (ex.: corrida) em erro de domínio."""
    try:
        with transaction.atomic():
            yield
    except IntegrityError as exc:
        if ResidentRecord.cpf_constraint_name() in str(exc):
            raise DuplicateCpfError(Resident.ROLE_LABEL) from exc
        raise


def _scoped(tenant_id):
    return ResidentRecord.objects.for_tenant(tenant_id)


def add(resident: Resident) -> Resident:
    record = ResidentRecord(tenant_id=resident.tenant_id)
    _apply(record, resident)
    with _cpf_violation_as_duplicate():
        record.save(force_insert=True)
    return resident.with_id(record.id)


def update(resident: Resident) -> Resident | None:
    record = _scoped(resident.tenant_id).filter(id=resident.id).first()
    if record is None:
        return None
    _apply(record, resident)
    with _cpf_violation_as_duplicate():
        record.save()
    return resident


def get(tenant_id, resident_id) -> Resident | None:
    record = _scoped(tenant_id).filter(id=resident_id).first()
    return _to_entity(record) if record else None


def list_for_tenant(tenant_id) -> list[Resident]:
    return [_to_entity(r) for r in _scoped(tenant_id).order_by(*ORDERING)]


def cpf_taken(tenant_id, cpf: str, exclude_id=None) -> bool:
    """Busca pelo hash, sem decifrar a tabela."""
    matches = _scoped(tenant_id).filter(cpf_hash=ResidentRecord.hash_cpf(cpf))
    if exclude_id is not None:
        matches = matches.exclude(id=exclude_id)
    return matches.exists()


def delete(tenant_id, resident_id) -> bool:
    deleted, _ = _scoped(tenant_id).filter(id=resident_id).delete()
    return deleted > 0


def count_by_apartment(tenant_id) -> dict:
    rows = _scoped(tenant_id).values("apartment_id").annotate(total=Count("id"))
    return {row["apartment_id"]: row["total"] for row in rows}


def count_in_apartment(tenant_id, apartment_id) -> int:
    return _scoped(tenant_id).filter(apartment_id=apartment_id).count()


def residences_by_cpf_hash(tenant_id, hashes) -> dict:
    return dict(_scoped(tenant_id).filter(cpf_hash__in=list(hashes)).values_list("cpf_hash", "apartment_id"))
