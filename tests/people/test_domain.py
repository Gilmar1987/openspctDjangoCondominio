import uuid
from dataclasses import dataclass

import pytest

from people.domain import (
    DuplicateCpfError,
    InvalidPersonError,
    Person,
    format_phone,
    is_valid_cpf,
    mask_cpf,
    normalize_text,
    only_digits,
)

TENANT = uuid.uuid4()


@pytest.mark.parametrize("value, expected", [(None, ""), ("", ""), ("529.982.247-25", "52998224725"), ("(81) 9 9999-0000", "81999990000")])
def test_only_digits(value, expected):
    assert only_digits(value) == expected


@pytest.mark.parametrize("value, expected", [(None, None), ("  ", None), ("  Maria  ", "Maria")])
def test_normalize_text(value, expected):
    assert normalize_text(value) == expected


@pytest.mark.parametrize("cpf", ["52998224725", "11144477735", "12345678909"])
def test_valid_cpf(cpf):
    assert is_valid_cpf(cpf)


@pytest.mark.parametrize("cpf", ["52998224726", "52998224715", "11111111111", "00000000000", "5299822472", "529982247250", "5299822472a"])
def test_invalid_cpf(cpf):
    assert not is_valid_cpf(cpf)


def test_mask_cpf():
    assert mask_cpf("52998224725") == "***.982.247-**"


@pytest.mark.parametrize("phone, expected", [("81999990000", "(81) 99999-0000"), ("8133334444", "(81) 3333-4444"), (None, None)])
def test_format_phone(phone, expected):
    assert format_phone(phone) == expected


def test_create_normalizes_general_attributes():
    person = Person.create(TENANT, name="  Maria Souza ", cpf="529.982.247-25", email="  maria@exemplo.com ", phone="(81) 99999-0000")

    assert person == Person(
        id=None, tenant_id=TENANT, name="Maria Souza", cpf="52998224725",
        email="maria@exemplo.com", phone="81999990000",
    )
    assert person.masked_cpf == "***.982.247-**"


def test_create_with_only_required_fields():
    person = Person.create(TENANT, name="Ana", cpf="52998224725", email="  ", phone="")

    assert (person.email, person.phone) == (None, None)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": "  ", "cpf": "52998224725"},
        {"name": "Ana", "cpf": "52998224726"},
        {"name": "Ana", "cpf": "52998224725", "phone": "1234"},
    ],
)
def test_create_rejects_invalid_attributes(kwargs):
    with pytest.raises(InvalidPersonError):
        Person.create(TENANT, **kwargs)


def test_update_keeps_identity_and_tenant():
    person_id = uuid.uuid4()
    person = Person.create(TENANT, name="Ana", cpf="52998224725").with_id(person_id)

    updated = person.update(name="Ana Lima", cpf="111.444.777-35", email=None, phone="8133334444")

    assert (updated.id, updated.tenant_id, updated.name, updated.cpf, updated.phone) == (
        person_id, TENANT, "Ana Lima", "11144477735", "8133334444",
    )


@dataclass(frozen=True)
class Resident(Person):
    ROLE_LABEL = "morador"


def test_subclass_inherits_create_and_update():
    resident = Resident.create(TENANT, name="Ana", cpf="52998224725")

    assert isinstance(resident, Resident)
    assert isinstance(resident.with_id(uuid.uuid4()).update(name="B", cpf="52998224725", email=None, phone=None), Resident)


def test_duplicate_cpf_message_uses_role_label():
    assert str(DuplicateCpfError(Resident.ROLE_LABEL)) == "Já existe morador com este CPF neste condomínio."
    assert Person.ROLE_LABEL == "pessoa"


@dataclass(frozen=True)
class WithUnit(Person):
    unit: str


def test_subclass_own_attributes_pass_through_create_and_update():
    person = WithUnit.create(TENANT, name="Ana", cpf="52998224725", unit="101")

    updated = person.with_id(uuid.uuid4()).update(name="Ana", cpf="52998224725", email=None, phone=None, unit="102")

    assert (person.unit, updated.unit) == ("101", "102")
    assert isinstance(updated, WithUnit)
