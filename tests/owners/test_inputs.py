import uuid

import pytest
from django.http import QueryDict

from owners.inputs import OwnerInput, parse_owner
from people.inputs import PersonInput

VALID = {"name": "Paulo", "cpf": "529.982.247-25"}
X, Y = uuid.uuid4(), uuid.uuid4()


def test_owner_input_extends_person_input():
    assert issubclass(OwnerInput, PersonInput)
    assert set(OwnerInput.model_fields) - set(PersonInput.model_fields) == {"apartment_ids"}


def test_inherited_validation_applies():
    _, errors = parse_owner({"name": "Paulo", "cpf": "111.111.111-11"})

    assert errors == {"cpf": ["O CPF informado é inválido."]}


def test_apartment_ids_from_json_list():
    data, errors = parse_owner({**VALID, "apartment_ids": [str(X), str(Y), str(X)]})

    assert errors is None
    assert data.apartment_ids == [X, Y]


def test_apartment_ids_default_to_empty():
    data, _ = parse_owner(VALID)

    assert data.apartment_ids == []


def test_apartment_ids_from_form_getlist():
    form = QueryDict(mutable=True)
    form.update({"name": "Paulo", "cpf": "52998224725"})
    form.setlist("apartment_ids", [str(X), "", str(Y)])

    data, errors = parse_owner(form)

    assert errors is None
    assert data.apartment_ids == [X, Y]


@pytest.mark.parametrize("value", [["nao-e-uuid"], "nao-e-lista", [123]])
def test_invalid_apartment_ids(value):
    _, errors = parse_owner({**VALID, "apartment_ids": value})

    assert errors == {"apartment_ids": ["Apartamento inválido."]}


def test_null_apartment_ids_is_empty():
    data, _ = parse_owner({**VALID, "apartment_ids": None})

    assert data.apartment_ids == []
