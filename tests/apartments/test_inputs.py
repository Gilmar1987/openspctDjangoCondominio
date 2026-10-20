import pytest

from apartments.inputs import parse_apartment

FLOOR_ERROR = {"floor": ["O andar deve ser um número inteiro entre -5 e 200."]}


def test_all_fields():
    data, errors = parse_apartment({"tower": " A ", "block": "1", "floor": 3, "number": "301"})

    assert errors is None
    assert (data.tower, data.block, data.floor, data.number) == ("A", "1", 3, "301")


def test_only_number():
    data, errors = parse_apartment({"number": "12"})

    assert errors is None
    assert (data.tower, data.block, data.floor, data.number) == (None, None, None, "12")


@pytest.mark.parametrize("payload", [{}, {"number": ""}, {"number": "   "}, {"number": None}])
def test_number_is_required(payload):
    data, errors = parse_apartment(payload)

    assert data is None
    assert errors == {"number": ["O campo número é obrigatório."]}


def test_number_over_limit():
    _, errors = parse_apartment({"number": "1" * 11})

    assert errors == {"number": ["O campo número deve ter no máximo 10 caracteres."]}


def test_tower_over_limit():
    _, errors = parse_apartment({"number": "1", "tower": "t" * 21})

    assert errors == {"tower": ["O campo torre deve ter no máximo 20 caracteres."]}


def test_block_over_limit():
    _, errors = parse_apartment({"number": "1", "block": "b" * 21})

    assert errors == {"block": ["O campo bloco deve ter no máximo 20 caracteres."]}


@pytest.mark.parametrize("floor", [201, -6, "terceiro", "3.5", 3.5, True, "201"])
def test_invalid_floor(floor):
    _, errors = parse_apartment({"number": "1", "floor": floor})

    assert errors == FLOOR_ERROR


@pytest.mark.parametrize("floor, expected", [("3", 3), (" -5 ", -5), (200, 200), (0, 0)])
def test_valid_floor(floor, expected):
    data, errors = parse_apartment({"number": "1", "floor": floor})

    assert errors is None
    assert data.floor == expected


@pytest.mark.parametrize("blank", ["", "   ", None])
def test_blank_optional_fields_become_absent(blank):
    data, _ = parse_apartment({"number": "1", "tower": blank, "block": blank, "floor": blank})

    assert (data.tower, data.block, data.floor) == (None, None, None)


def test_extra_tenant_field_is_ignored():
    data, errors = parse_apartment({"number": "1", "tenant": "outro", "tenant_id": "outro"})

    assert errors is None
    assert not hasattr(data, "tenant") and not hasattr(data, "tenant_id")


def test_non_object_body_reports_required_number():
    _, errors = parse_apartment(["101"])

    assert errors == {"number": ["O campo número é obrigatório."]}
