import uuid
from dataclasses import fields

import pytest

from owners.domain import (
    ApartmentNotFoundError,
    ApartmentTakenError,
    Owner,
    plan_apartment_links,
)
from people.domain import DuplicateCpfError, Person

TENANT = uuid.uuid4()
OWNER = uuid.uuid4()
OTHER = uuid.uuid4()
X, Y, Z = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()


def test_owner_inherits_person_without_redeclaring_attributes():
    assert issubclass(Owner, Person)
    assert [f.name for f in fields(Owner)] == [f.name for f in fields(Person)]


def test_owner_uses_inherited_create_and_update():
    owner = Owner.create(TENANT, name=" Paulo ", cpf="529.982.247-25", phone="(81) 3333-4444")

    assert isinstance(owner, Owner)
    assert (owner.name, owner.cpf, owner.phone) == ("Paulo", "52998224725", "8133334444")
    assert isinstance(owner.with_id(OWNER).update(name="Paulo", cpf="52998224725", email=None, phone=None), Owner)


def test_owner_role_label():
    assert str(DuplicateCpfError(Owner.ROLE_LABEL)) == "Já existe proprietário com este CPF neste condomínio."


def test_plan_links_free_apartments_for_new_owner():
    to_assign, to_release = plan_apartment_links(
        None, [X, Y], {X: ("Nº 101", None), Y: ("Nº 102", None)}, currently_owned=set()
    )

    assert (to_assign, to_release) == ({X, Y}, set())


def test_plan_keeps_own_and_releases_removed():
    to_assign, to_release = plan_apartment_links(
        OWNER, [X, Z], {X: ("Nº 101", OWNER), Z: ("Nº 103", None)}, currently_owned={X, Y}
    )

    assert (to_assign, to_release) == ({Z}, {Y})


def test_plan_empty_selection_releases_everything():
    assert plan_apartment_links(OWNER, [], {}, currently_owned={X}) == (set(), {X})


def test_plan_rejects_apartment_not_found():
    with pytest.raises(ApartmentNotFoundError) as exc:
        plan_apartment_links(OWNER, [X], {}, currently_owned=set())
    assert str(exc.value) == "O apartamento não foi encontrado neste condomínio."


@pytest.mark.parametrize("owner_id", [None, OWNER])
def test_plan_rejects_apartment_of_other_owner(owner_id):
    with pytest.raises(ApartmentTakenError) as exc:
        plan_apartment_links(owner_id, [X], {X: ("Torre A · Nº 101", OTHER)}, currently_owned=set())
    assert str(exc.value) == "O apartamento Torre A · Nº 101 já tem outro proprietário."
