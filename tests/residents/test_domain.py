import uuid
from dataclasses import fields

import pytest

from people.domain import DuplicateCpfError, Person
from residents.domain import InvalidResidentError, Resident

TENANT = uuid.uuid4()
APARTMENT = uuid.uuid4()
OTHER_APARTMENT = uuid.uuid4()


def test_resident_inherits_person_and_adds_only_apartment():
    assert issubclass(Resident, Person)
    person_fields = [f.name for f in fields(Person)]
    assert [f.name for f in fields(Resident)] == [*person_fields, "apartment_id"]


def test_role_label_and_duplicate_message():
    assert Resident.ROLE_LABEL == "morador"
    assert str(DuplicateCpfError(Resident.ROLE_LABEL)) == "Já existe morador com este CPF neste condomínio."


def test_create_normalizes_inherited_attributes_and_keeps_apartment():
    resident = Resident.create(TENANT, name=" João ", cpf="390.533.447-05", phone="(81) 98888-1111", apartment_id=APARTMENT)

    assert isinstance(resident, Resident)
    assert (resident.name, resident.cpf, resident.phone, resident.apartment_id) == (
        "João", "39053344705", "81988881111", APARTMENT,
    )


def test_update_changes_apartment():
    resident = Resident.create(TENANT, name="João", cpf="39053344705", apartment_id=APARTMENT).with_id(uuid.uuid4())

    moved = resident.update(name="João", cpf="39053344705", email=None, phone=None, apartment_id=OTHER_APARTMENT)

    assert (moved.id, moved.apartment_id) == (resident.id, OTHER_APARTMENT)


@pytest.mark.parametrize("apartment_id", [None])
def test_apartment_is_required(apartment_id):
    with pytest.raises(InvalidResidentError):
        Resident.create(TENANT, name="João", cpf="39053344705", apartment_id=apartment_id)


def test_apartment_is_required_on_update():
    resident = Resident.create(TENANT, name="João", cpf="39053344705", apartment_id=APARTMENT)

    with pytest.raises(InvalidResidentError):
        resident.update(name="João", cpf="39053344705", email=None, phone=None, apartment_id=None)
