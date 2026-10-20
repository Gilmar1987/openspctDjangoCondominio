"""Persistência de proprietários: toda consulta parte de for_tenant() (ADR-0007, ADR-0013)."""

from contextlib import contextmanager

from django.db import IntegrityError, transaction
from django.db.models.functions import Lower

from owners.domain import Owner
from owners.models import OwnerRecord
from people.domain import DuplicateCpfError

ORDERING = (Lower("name"), "name")


def _to_entity(record) -> Owner:
    return Owner(
        id=record.id,
        tenant_id=record.tenant_id,
        name=record.name,
        cpf=record.get_cpf(),
        email=record.email,
        phone=record.phone,
    )


def _apply(record, owner: Owner) -> None:
    record.name = owner.name
    record.email = owner.email
    record.phone = owner.phone
    record.set_cpf(owner.cpf)


@contextmanager
def _cpf_violation_as_duplicate():
    """Converte a violação da unicidade de CPF (ex.: corrida) em erro de domínio."""
    try:
        with transaction.atomic():
            yield
    except IntegrityError as exc:
        if OwnerRecord.cpf_constraint_name() in str(exc):
            raise DuplicateCpfError(Owner.ROLE_LABEL) from exc
        raise


def _scoped(tenant_id):
    return OwnerRecord.objects.for_tenant(tenant_id)


def add(owner: Owner) -> Owner:
    record = OwnerRecord(tenant_id=owner.tenant_id)
    _apply(record, owner)
    with _cpf_violation_as_duplicate():
        record.save(force_insert=True)
    return owner.with_id(record.id)


def update(owner: Owner) -> Owner | None:
    record = _scoped(owner.tenant_id).filter(id=owner.id).first()
    if record is None:
        return None
    _apply(record, owner)
    with _cpf_violation_as_duplicate():
        record.save()
    return owner


def get(tenant_id, owner_id) -> Owner | None:
    record = _scoped(tenant_id).filter(id=owner_id).first()
    return _to_entity(record) if record else None


def list_for_tenant(tenant_id) -> list[Owner]:
    return [_to_entity(r) for r in _scoped(tenant_id).order_by(*ORDERING)]


def cpf_taken(tenant_id, cpf: str, exclude_id=None) -> bool:
    """Busca pelo hash, sem decifrar a tabela."""
    matches = _scoped(tenant_id).filter(cpf_hash=OwnerRecord.hash_cpf(cpf))
    if exclude_id is not None:
        matches = matches.exclude(id=exclude_id)
    return matches.exists()


def names_by_id(tenant_id, owner_ids) -> dict:
    return dict(_scoped(tenant_id).filter(id__in=list(owner_ids)).values_list("id", "name"))


def by_cpf_hashes(tenant_id, hashes) -> list[tuple]:
    """(hash, id, nome) dos proprietários com esses hashes de CPF, sem decifrar (ADR-0017)."""
    return list(_scoped(tenant_id).filter(cpf_hash__in=list(hashes)).values_list("cpf_hash", "id", "name"))


def delete(tenant_id, owner_id) -> bool:
    deleted, _ = _scoped(tenant_id).filter(id=owner_id).delete()
    return deleted > 0
