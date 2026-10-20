import uuid

import pytest

from apartments.domain import (
    Apartment,
    DuplicateApartmentError,
    InvalidApartmentError,
    ensure_unique,
    normalize_text,
)

TENANT = uuid.uuid4()


@pytest.mark.parametrize(
    "value, expected",
    [(None, None), ("", None), ("   ", None), ("  A  ", "A"), ("101", "101")],
)
def test_normalize_text(value, expected):
    assert normalize_text(value) == expected


def test_create_normalizes_fields():
    apartment = Apartment.create(TENANT, number=" 301 ", tower=" A ", block="  ", floor=3)

    assert apartment == Apartment(
        id=None, tenant_id=TENANT, tower="A", block=None, floor=3, number="301"
    )


def test_create_requires_number():
    with pytest.raises(InvalidApartmentError):
        Apartment.create(TENANT, number="   ")


def test_update_keeps_identity_and_tenant():
    apartment_id = uuid.uuid4()
    apartment = Apartment.create(TENANT, number="301", floor=3).with_id(apartment_id)

    updated = apartment.update(number="302", tower="B", block=None, floor=4)

    assert updated == Apartment(
        id=apartment_id, tenant_id=TENANT, tower="B", block=None, floor=4, number="302"
    )


def test_update_requires_number():
    apartment = Apartment.create(TENANT, number="301")

    with pytest.raises(InvalidApartmentError):
        apartment.update(number="", tower=None, block=None, floor=None)


def test_natural_key_ignores_case_and_treats_absent_as_equal():
    first = Apartment.create(TENANT, number="101A", tower="Torre a")
    second = Apartment.create(TENANT, number="101a", tower="TORRE A", floor=9)

    assert first.natural_key == second.natural_key == ("torre a", "", "101a")


def test_ensure_unique_rejects_other_apartment_with_same_key():
    existing = Apartment.create(TENANT, number="101", tower="A").with_id(uuid.uuid4())
    candidate = Apartment.create(TENANT, number="101", tower="a")

    with pytest.raises(DuplicateApartmentError) as exc:
        ensure_unique(candidate, [existing])
    assert str(exc.value) == "Este apartamento já existe neste condomínio."


def test_ensure_unique_ignores_the_apartment_itself():
    apartment = Apartment.create(TENANT, number="101", tower="A").with_id(uuid.uuid4())

    ensure_unique(apartment.update(number="101", tower="A", block=None, floor=2), [apartment])


def test_ensure_unique_allows_different_key():
    existing = Apartment.create(TENANT, number="101", tower="A").with_id(uuid.uuid4())

    ensure_unique(Apartment.create(TENANT, number="101", tower="B"), [existing])
