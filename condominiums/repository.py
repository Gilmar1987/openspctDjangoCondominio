from django.db.models.functions import Lower

from condominiums.domain import Condominium
from tenancy.public import Condominium as CondominiumRecord


def _to_entity(record) -> Condominium:
    return Condominium(id=record.id, name=record.name)


def add(condominium: Condominium) -> Condominium:
    record = CondominiumRecord.objects.create(name=condominium.name)
    return condominium.with_id(record.id)


def list_all() -> list[Condominium]:
    return [_to_entity(r) for r in CondominiumRecord.objects.order_by(Lower("name"), "name")]


def get(condominium_id) -> Condominium | None:
    record = CondominiumRecord.objects.filter(id=condominium_id).first()
    return _to_entity(record) if record else None
