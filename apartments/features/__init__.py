from apartments.domain import Apartment, DuplicateApartmentError

DUPLICATE_FIELD = "apartment"


def as_json(apartment: Apartment) -> dict:
    return {
        "id": str(apartment.id),
        "condominium_id": str(apartment.tenant_id),
        "tower": apartment.tower,
        "block": apartment.block,
        "floor": apartment.floor,
        "number": apartment.number,
    }


def form_values(apartment: Apartment) -> dict:
    return {
        "tower": apartment.tower,
        "block": apartment.block,
        "floor": apartment.floor,
        "number": apartment.number,
    }


def duplicate_errors(exc: DuplicateApartmentError) -> dict[str, list[str]]:
    return {DUPLICATE_FIELD: [str(exc)]}
