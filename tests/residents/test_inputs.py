import uuid

import pytest

from people.inputs import PersonInput
from residents.inputs import ResidentInput, parse_resident

APARTMENT = uuid.uuid4()
VALID = {"name": "João", "cpf": "390.533.447-05", "apartment_id": str(APARTMENT)}


def test_resident_input_extends_person_input_with_apartment_only():
    assert issubclass(ResidentInput, PersonInput)
    assert set(ResidentInput.model_fields) - set(PersonInput.model_fields) == {"apartment_id"}


def test_valid_input():
    data, errors = parse_resident(VALID)

    assert errors is None
    assert (data.cpf, data.apartment_id) == ("39053344705", APARTMENT)


@pytest.mark.parametrize("value", [None, "", "  "])
def test_apartment_is_required(value):
    _, errors = parse_resident({**VALID, "apartment_id": value})

    assert errors == {"apartment_id": ["O campo apartamento é obrigatório."]}


def test_apartment_missing_key():
    _, errors = parse_resident({"name": "João", "cpf": "39053344705"})

    assert errors == {"apartment_id": ["O campo apartamento é obrigatório."]}


def test_invalid_apartment_uuid():
    _, errors = parse_resident({**VALID, "apartment_id": "nao-e-uuid"})

    assert errors == {"apartment_id": ["O apartamento não foi encontrado neste condomínio."]}


def test_inherited_validation_applies():
    _, errors = parse_resident({**VALID, "cpf": "390.533.447-06"})

    assert errors == {"cpf": ["O CPF informado é inválido."]}
