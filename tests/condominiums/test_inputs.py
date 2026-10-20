import pytest

from condominiums.inputs import parse_condominium


def test_valid_name_is_stripped():
    data, errors = parse_condominium({"name": "  Residencial Aurora "})

    assert errors is None
    assert data.name == "Residencial Aurora"


@pytest.mark.parametrize("payload", [{}, {"name": ""}, {"name": "   "}])
def test_name_is_required(payload):
    data, errors = parse_condominium(payload)

    assert data is None
    assert errors == {"name": ["O campo nome é obrigatório."]}


def test_name_with_120_characters_is_accepted():
    data, errors = parse_condominium({"name": "a" * 120})

    assert errors is None
    assert len(data.name) == 120


def test_name_with_121_characters_is_rejected():
    _, errors = parse_condominium({"name": "a" * 121})

    assert errors == {"name": ["O campo nome deve ter no máximo 120 caracteres."]}
