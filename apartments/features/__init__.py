from typing import Optional

from apartments.domain import Apartment, DuplicateApartmentError
from apartments.inputs import OWNER_NOT_FOUND
from owners import public as owners
from tenancy.public import TenantRef

DUPLICATE_FIELD = "apartment"


class OwnerNotFoundError(Exception):
    def __init__(self):
        super().__init__(OWNER_NOT_FOUND)


def check_owner(tenant: TenantRef, owner_id) -> None:
    """O proprietário, quando informado, precisa existir no mesmo condomínio (ADR-0015)."""
    if owner_id is not None and owners.get_owner(tenant.id, owner_id) is None:
        raise OwnerNotFoundError()


def owner_names(tenant: TenantRef, apartments: list[Apartment]) -> dict:
    ids = {a.owner_id for a in apartments if a.owner_id is not None}
    return owners.names_by_id(tenant.id, ids) if ids else {}


def as_json(apartment: Apartment, owner_name: Optional[str] = None) -> dict:
    return {
        "id": str(apartment.id),
        "condominium_id": str(apartment.tenant_id),
        "tower": apartment.tower,
        "block": apartment.block,
        "floor": apartment.floor,
        "number": apartment.number,
        "owner_id": str(apartment.owner_id) if apartment.owner_id else None,
        "owner_name": owner_name,
    }


def as_json_with_owner(tenant: TenantRef, apartment: Apartment) -> dict:
    return as_json(apartment, owner_names(tenant, [apartment]).get(apartment.owner_id))


def form_values(apartment: Apartment) -> dict:
    return {
        "tower": apartment.tower,
        "block": apartment.block,
        "floor": apartment.floor,
        "number": apartment.number,
        "owner_id": apartment.owner_id,
    }


def form_context(tenant: TenantRef) -> dict:
    return {"owners": owners.list_owners(tenant.id)}


def duplicate_errors(exc: DuplicateApartmentError) -> dict[str, list[str]]:
    return {DUPLICATE_FIELD: [str(exc)]}


def owner_errors(exc: OwnerNotFoundError) -> dict[str, list[str]]:
    return {"owner_id": [str(exc)]}
