import uuid

import pytest

from apartments import repository
from apartments.domain import Apartment, DuplicateApartmentError

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def tenant(make_condominium):
    return make_condominium("Aurora").id


@pytest.fixture
def other_tenant(make_condominium):
    return make_condominium("Solar").id


def add(tenant_id, number, tower=None, block=None, floor=None):
    return repository.add(Apartment.create(tenant_id, number, tower, block, floor))


def test_add_and_get(tenant):
    created = add(tenant, "301", tower="A", block="1", floor=3)

    assert isinstance(created.id, uuid.UUID)
    assert repository.get(tenant, created.id) == created


def test_get_from_other_tenant_is_none(tenant, other_tenant):
    created = add(tenant, "301")

    assert repository.get(other_tenant, created.id) is None


def test_list_only_returns_rows_of_the_tenant(tenant, other_tenant):
    add(tenant, "101")
    add(other_tenant, "202")

    assert [a.number for a in repository.list_for_tenant(tenant)] == ["101"]
    assert [a.number for a in repository.list_for_tenant(other_tenant)] == ["202"]


def test_database_rejects_duplicate_ignoring_case_and_absent_fields(tenant):
    add(tenant, "101A", tower="Torre A")

    with pytest.raises(DuplicateApartmentError):
        add(tenant, "101a", tower="TORRE A", floor=7)


def test_database_treats_absent_tower_and_block_as_equal(tenant):
    add(tenant, "12")

    with pytest.raises(DuplicateApartmentError):
        add(tenant, "12")


def test_same_number_in_other_tower_or_other_tenant_is_allowed(tenant, other_tenant):
    add(tenant, "101", tower="A")
    add(tenant, "101", tower="B")
    add(other_tenant, "101", tower="A")

    assert len(repository.list_for_tenant(tenant)) == 2
    assert len(repository.list_for_tenant(other_tenant)) == 1


def test_find_same_key_returns_matches_only_in_tenant(tenant, other_tenant):
    existing = add(tenant, "101", tower="A")
    add(other_tenant, "101", tower="A")
    add(tenant, "102", tower="A")

    matches = repository.find_same_key(Apartment.create(tenant, "101", tower="a"))

    assert matches == [existing]


def test_update_to_duplicate_is_rejected_and_row_kept(tenant):
    add(tenant, "101")
    second = add(tenant, "102")

    with pytest.raises(DuplicateApartmentError):
        repository.update(second.update(number="101", tower=None, block=None, floor=None))
    assert repository.get(tenant, second.id).number == "102"


def test_update_persists_changes(tenant):
    created = add(tenant, "301", floor=3)

    repository.update(created.update(number="301", tower=None, block=None, floor=4))

    assert repository.get(tenant, created.id).floor == 4


def test_update_of_apartment_from_other_tenant_changes_nothing(tenant, other_tenant):
    created = add(tenant, "301")
    forged = Apartment(id=created.id, tenant_id=other_tenant, tower=None, block=None, floor=None, number="999")

    assert repository.update(forged) is None
    assert repository.get(tenant, created.id).number == "301"


def test_delete(tenant, other_tenant):
    created = add(tenant, "301")

    assert repository.delete(other_tenant, created.id) is False
    assert repository.delete(tenant, created.id) is True
    assert repository.get(tenant, created.id) is None


def test_list_order_absent_first_then_tower_block_floor_number(tenant):
    add(tenant, "101", tower="B")
    add(tenant, "100", tower="A", block="1", floor=1)
    add(tenant, "201", tower="A", floor=2)
    add(tenant, "12", tower="A", floor=1)
    add(tenant, "101", tower="A", floor=1)
    add(tenant, "5")

    listed = [(a.tower, a.block, a.floor, a.number) for a in repository.list_for_tenant(tenant)]

    assert listed == [
        (None, None, None, "5"),
        ("A", None, 1, "101"),
        ("A", None, 1, "12"),  # ordem lexicográfica do número, aceita no MVP
        ("A", None, 2, "201"),
        ("A", "1", 1, "100"),
        ("B", None, None, "101"),
    ]
