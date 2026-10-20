"""Operações compartilhadas pelas fatias de moradores.

Apartamento e proprietário são consultados só por `apartments.public` e `owners.public`
(ADR-0015). O vínculo com proprietário é reconhecido pelo hash do CPF, sem decifrar nada
(ADR-0017). Logs registram identificadores e nomes de campo, nunca valores (ADR-0009).
"""

import logging
from typing import Optional

from django.db import transaction
from django.http import Http404

from apartments import public as apartments
from owners import public as owners
from people.domain import DuplicateCpfError, format_phone
from people.models import PersonModel
from residents import repository
from residents.domain import Resident
from residents.inputs import APARTMENT_NOT_FOUND
from tenancy.public import TenantRef

logger = logging.getLogger("residents")


class ApartmentNotFoundError(Exception):
    def __init__(self):
        super().__init__(APARTMENT_NOT_FOUND)


BUSINESS_ERRORS = (DuplicateCpfError, ApartmentNotFoundError)


def business_errors(exc) -> dict[str, list[str]]:
    field = "cpf" if isinstance(exc, DuplicateCpfError) else "apartment_id"
    return {field: [str(exc)]}


def log_rejected(tenant: TenantRef, errors: dict) -> None:
    logger.info("resident rejected tenant=%s fields=%s", tenant.id, sorted(errors))


def save_resident(tenant: TenantRef, resident: Resident) -> Resident:
    with transaction.atomic():
        if not apartments.get_many(tenant.id, [resident.apartment_id]):
            raise ApartmentNotFoundError()
        if repository.cpf_taken(tenant.id, resident.cpf, exclude_id=resident.id):
            raise DuplicateCpfError(Resident.ROLE_LABEL)
        saved = repository.add(resident) if resident.id is None else repository.update(resident)
        if saved is None:
            raise Http404
    return saved


def context_for(tenant: TenantRef, residents: list[Resident]) -> tuple[dict, dict]:
    """Rótulos dos apartamentos e, por morador, o vínculo de proprietário (ADR-0017)."""
    labels = {a.id: a.label for a in apartments.get_many(tenant.id, {r.apartment_id for r in residents}).values()}
    hashes = {r.id: PersonModel.hash_cpf(r.cpf) for r in residents}
    owners_by_hash = owners.owners_by_cpf_hash(tenant.id, set(hashes.values()))
    counts = apartments.count_by_owner(tenant.id) if owners_by_hash else {}
    also_owner = {}
    for resident in residents:
        owner = owners_by_hash.get(hashes[resident.id])
        if owner is not None:
            also_owner[resident.id] = {"owner_id": str(owner.id), "apartment_count": counts.get(owner.id, 0)}
    return labels, also_owner


def as_json(resident: Resident, label: str, also_owner: Optional[dict], include_cpf: bool = False) -> dict:
    body = {
        "id": str(resident.id),
        "condominium_id": str(resident.tenant_id),
        "name": resident.name,
        "cpf_masked": resident.masked_cpf,
        "email": resident.email,
        "phone": resident.phone,
        "apartment": {"id": str(resident.apartment_id), "label": label},
        "also_owner": also_owner,
    }
    if include_cpf:
        body["cpf"] = resident.cpf
    return body


def detail_json(tenant: TenantRef, resident: Resident, include_cpf: bool = False) -> dict:
    labels, also_owner = context_for(tenant, [resident])
    return as_json(resident, labels.get(resident.apartment_id), also_owner.get(resident.id), include_cpf)


def display(resident: Resident, label: str, also_owner: Optional[dict]) -> dict:
    """Dados para as páginas: CPF sempre mascarado e telefone formatado."""
    return {
        "id": resident.id,
        "name": resident.name,
        "cpf_masked": resident.masked_cpf,
        "email": resident.email,
        "phone": format_phone(resident.phone),
        "apartment_label": label,
        "also_owner": also_owner,
    }


def form_context(tenant: TenantRef) -> dict:
    return {"apartments": apartments.list_all(tenant.id), "owners": owners.list_owners(tenant.id)}
