import uuid

import pytest

from condominiums.domain import Condominium, InvalidCondominiumError


def test_create_strips_name():
    condominium = Condominium.create("  Residencial Aurora  ")

    assert condominium.name == "Residencial Aurora"
    assert condominium.id is None


def test_create_rejects_blank_name():
    with pytest.raises(InvalidCondominiumError):
        Condominium.create("   ")


def test_with_id_keeps_name():
    condominium_id = uuid.uuid4()

    assert Condominium.create("Solar").with_id(condominium_id) == Condominium(
        id=condominium_id, name="Solar"
    )
