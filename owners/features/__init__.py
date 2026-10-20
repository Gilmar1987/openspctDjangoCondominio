"""Operações compartilhadas pelas fatias de proprietários.

O vínculo com apartamentos passa só por `apartments.public` e roda numa única transação
(ADR-0015). Os logs registram identificadores e nomes de campo, nunca valores (ADR-0009).
"""

import logging
from typing import Optional

from django.db import transaction
from django.http import Http404

from apartments import public as apartments
from owners import repository
from owners.domain import ApartmentNotFoundError, ApartmentTakenError, Owner, plan_apartment_links
from people.domain import DuplicateCpfError, format_phone
from people.models import PersonModel
from residents import public as residents
from tenancy.public import TenantRef

logger = logging.getLogger("owners")

BUSINESS_ERRORS = (DuplicateCpfError, ApartmentNotFoundError, ApartmentTakenError)


def business_errors(exc) -> dict[str, list[str]]:
    field = "cpf" if isinstance(exc, DuplicateCpfError) else "apartment_ids"
    return {field: [str(exc)]}


def log_rejected(tenant: TenantRef, errors: dict) -> None:
    logger.info("owner rejected tenant=%s fields=%s", tenant.id, sorted(errors))


def save_owner(tenant: TenantRef, owner: Owner, apartment_ids: list) -> Owner:
    """Grava o proprietário e o seu conjunto de apartamentos atomicamente."""
    with transaction.atomic():
        if repository.cpf_taken(tenant.id, owner.cpf, exclude_id=owner.id):
            raise DuplicateCpfError(Owner.ROLE_LABEL)
        found = apartments.get_many(tenant.id, apartment_ids)
        currently_owned = {a.id for a in apartments.list_by_owner(tenant.id, owner.id)} if owner.id else set()
        to_assign, _ = plan_apartment_links(
            owner.id, apartment_ids, {i: (r.label, r.owner_id) for i, r in found.items()}, currently_owned
        )
        saved = repository.add(owner) if owner.id is None else repository.update(owner)
        if saved is None:
            raise Http404
        for apartment_id in sorted(to_assign, key=lambda i: found[i].label):
            # UPDATE condicional: se outro dono tomou a unidade desde a checagem, desfaz tudo.
            if apartments.assign_owner(tenant.id, [apartment_id], saved.id) != 1:
                raise ApartmentTakenError(found[apartment_id].label)
        apartments.release_owner(tenant.id, saved.id, keep_ids=apartment_ids)
    return saved


def residences(tenant: TenantRef, owners: list[Owner]) -> dict:
    """Apartamento onde cada proprietário mora, quando também é morador (ADR-0017).

    O reconhecimento é pelo hash do CPF no mesmo condomínio; nenhum CPF é decifrado ou trafegado.
    """
    hashes = {o.id: PersonModel.hash_cpf(o.cpf) for o in owners}
    homes = residents.residences_by_cpf_hash(tenant.id, set(hashes.values()))
    if not homes:
        return {}
    labels = apartments.get_many(tenant.id, set(homes.values()))
    result = {}
    for owner_id, digest in hashes.items():
        apartment_id = homes.get(digest)
        if apartment_id in labels:
            result[owner_id] = {"id": str(apartment_id), "label": labels[apartment_id].label}
    return result


def list_json(owner: Owner, apartment_count: int, resident_of: Optional[dict] = None) -> dict:
    return {
        "id": str(owner.id),
        "name": owner.name,
        "cpf_masked": owner.masked_cpf,
        "email": owner.email,
        "phone": owner.phone,
        "apartment_count": apartment_count,
        "resident_of": resident_of,
    }


def detail_json(tenant: TenantRef, owner: Owner, include_cpf: bool = False) -> dict:
    body = {
        "id": str(owner.id),
        "condominium_id": str(owner.tenant_id),
        "name": owner.name,
        "cpf_masked": owner.masked_cpf,
        "email": owner.email,
        "phone": owner.phone,
        "apartments": [{"id": str(a.id), "label": a.label} for a in apartments.list_by_owner(tenant.id, owner.id)],
        "resident_of": residences(tenant, [owner]).get(owner.id),
    }
    if include_cpf:
        body["cpf"] = owner.cpf
    return body


def display(owner: Owner, resident_of: Optional[dict] = None) -> dict:
    """Dados para as páginas: CPF sempre mascarado e telefone formatado."""
    return {
        "id": owner.id,
        "name": owner.name,
        "cpf_masked": owner.masked_cpf,
        "email": owner.email,
        "phone": format_phone(owner.phone),
        "resident_of": resident_of,
    }


def form_options(tenant: TenantRef, owner_id=None) -> list:
    return apartments.list_selectable_for_owner(tenant.id, owner_id)
