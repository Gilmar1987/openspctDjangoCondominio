import uuid

import pytest

from apartments import public
from apartments.models import ApartmentRecord
from tests.conftest import CPF_ANA

pytestmark = pytest.mark.django_db


@pytest.fixture
def paulo(condo, make_owner):
    return make_owner(condo, "Paulo")


@pytest.fixture
def ana(condo, make_owner):
    return make_owner(condo, "Ana", CPF_ANA)


def owner_of(apartment):
    return ApartmentRecord.objects.get(id=apartment.id).owner_id


def test_label_omits_absent_fields(condo, make_apartment):
    full = make_apartment(condo, "301", tower="A", block="1")
    only_number = make_apartment(condo, "12")

    refs = public.get_many(condo.id, [full.id, only_number.id])

    assert refs[full.id].label == "Torre A · Bloco 1 · Nº 301"
    assert refs[only_number.id] == public.ApartmentRef(id=only_number.id, label="Nº 12", owner_id=None)


def test_get_many_ignores_other_condominium_and_unknown(condo, other_condo, make_apartment):
    foreign = make_apartment(other_condo, "101")

    assert public.get_many(condo.id, [foreign.id, uuid.uuid4()]) == {}


def test_selectable_for_owner_lists_free_and_own(condo, other_condo, make_apartment, paulo, ana):
    free = make_apartment(condo, "101")
    own = make_apartment(condo, "102", owner=paulo)
    make_apartment(condo, "103", owner=ana)
    make_apartment(other_condo, "104")

    assert [a.id for a in public.list_selectable_for_owner(condo.id, paulo.id)] == [free.id, own.id]
    assert [a.id for a in public.list_selectable_for_owner(condo.id, None)] == [free.id]


def test_list_and_count_by_owner(condo, make_apartment, paulo, ana):
    first = make_apartment(condo, "101", owner=paulo)
    second = make_apartment(condo, "102", owner=paulo)
    make_apartment(condo, "103")

    assert [a.id for a in public.list_by_owner(condo.id, paulo.id)] == [first.id, second.id]
    assert public.count_by_owner(condo.id) == {paulo.id: 2}


def test_assign_owner_only_takes_free_or_own(condo, make_apartment, paulo, ana):
    free = make_apartment(condo, "101")
    own = make_apartment(condo, "102", owner=paulo)
    taken = make_apartment(condo, "103", owner=ana)

    updated = public.assign_owner(condo.id, [free.id, own.id, taken.id], paulo.id)

    assert updated == 2
    assert (owner_of(free), owner_of(own), owner_of(taken)) == (paulo.id, paulo.id, ana.id)


def test_assign_owner_is_restricted_to_condominium(condo, other_condo, make_apartment, paulo):
    foreign = make_apartment(other_condo, "101")

    assert public.assign_owner(condo.id, [foreign.id], paulo.id) == 0
    assert owner_of(foreign) is None


def test_release_owner_keeps_selected(condo, make_apartment, paulo, ana):
    kept = make_apartment(condo, "101", owner=paulo)
    released = make_apartment(condo, "102", owner=paulo)
    other = make_apartment(condo, "103", owner=ana)

    assert public.release_owner(condo.id, paulo.id, keep_ids=[kept.id]) == 1
    assert (owner_of(kept), owner_of(released), owner_of(other)) == (paulo.id, None, ana.id)


def test_release_owner_all(condo, make_apartment, paulo):
    make_apartment(condo, "101", owner=paulo)

    assert public.release_owner(condo.id, paulo.id) == 1
    assert public.list_by_owner(condo.id, paulo.id) == []
