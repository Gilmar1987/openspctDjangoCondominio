import pytest

from people.inputs import PersonInput, parse_person

VALID = {"name": "Maria Souza", "cpf": "529.982.247-25"}


def test_all_fields_are_normalized():
    data, errors = parse_person(
        PersonInput,
        {**VALID, "name": "  Maria Souza ", "email": " maria@exemplo.com ", "phone": "(81) 99999-0000"},
    )

    assert errors is None
    assert (data.name, data.cpf, data.email, data.phone) == ("Maria Souza", "52998224725", "maria@exemplo.com", "81999990000")


def test_blank_optional_fields_become_absent():
    data, _ = parse_person(PersonInput, {**VALID, "email": "  ", "phone": ""})

    assert (data.email, data.phone) == (None, None)


@pytest.mark.parametrize("payload, field, message", [
    ({"cpf": "52998224725"}, "name", "O campo nome é obrigatório."),
    ({"name": "  ", "cpf": "52998224725"}, "name", "O campo nome é obrigatório."),
    ({"name": "a" * 121, "cpf": "52998224725"}, "name", "O campo nome deve ter no máximo 120 caracteres."),
    ({"name": "Ana"}, "cpf", "O campo CPF é obrigatório."),
    ({"name": "Ana", "cpf": "  "}, "cpf", "O campo CPF é obrigatório."),
    ({"name": "Ana", "cpf": "529.982.247-26"}, "cpf", "O CPF informado é inválido."),
    ({"name": "Ana", "cpf": "111.111.111-11"}, "cpf", "O CPF informado é inválido."),
    ({**VALID, "email": "maria@"}, "email", "O e-mail informado é inválido."),
    ({**VALID, "email": "a" * 250 + "@x.com"}, "email", "O campo e-mail deve ter no máximo 254 caracteres."),
    ({**VALID, "phone": "1234"}, "phone", "O telefone deve ter DDD e 8 ou 9 dígitos."),
])
def test_invalid_input(payload, field, message):
    data, errors = parse_person(PersonInput, payload)

    assert data is None
    assert errors[field] == [message]


def test_cpf_with_non_text_type():
    _, errors = parse_person(PersonInput, {"name": "Ana", "cpf": 52998224725})

    assert errors == {"cpf": ["O campo CPF deve ser um texto."]}


def test_non_object_body_reports_required_fields():
    _, errors = parse_person(PersonInput, ["x"])

    assert set(errors) == {"name", "cpf"}
