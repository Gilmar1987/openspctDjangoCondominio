"""Delta de `proprietarios` em cadastro-de-moradores: proprietário que também é morador."""

import pytest

from tests.conftest import CPF_ANA, CPF_PAULO

pytestmark = pytest.mark.django_db


@pytest.fixture
def paulo_resident(condo, make_owner, make_apartment, make_resident):
    paulo = make_owner(condo, "Paulo", CPF_PAULO)
    a101 = make_apartment(condo, "101", tower="A", owner=paulo)
    make_apartment(condo, "102", tower="A", owner=paulo)
    make_resident(condo, a101, "Paulo", CPF_PAULO)
    return paulo, a101


def test_api_list_and_detail_show_resident_of(api_client, condo, paulo_resident, make_owner):
    paulo, a101 = paulo_resident
    make_owner(condo, "Ana", CPF_ANA)
    base = f"/api/condominios/{condo.id}/proprietarios/"

    listed = {o["name"]: o["resident_of"] for o in api_client.get(base).json()}
    detail = api_client.get(f"{base}{paulo.id}/").json()

    expected = {"id": str(a101.id), "label": "Torre A · Nº 101"}
    assert listed == {"Ana": None, "Paulo": expected}
    assert detail["resident_of"] == expected


def test_pages_show_resident_of(client, condo, paulo_resident):
    paulo, _ = paulo_resident
    base = f"/condominios/{condo.id}/proprietarios/"

    assert "também é morador de Torre A · Nº 101" in client.get(base).content.decode()
    assert "também é morador de Torre A · Nº 101" in client.get(f"{base}{paulo.id}/").content.decode()


def test_owner_without_resident_record(api_client, client, condo, make_owner):
    ana = make_owner(condo, "Ana", CPF_ANA)

    assert api_client.get(f"/api/condominios/{condo.id}/proprietarios/{ana.id}/").json()["resident_of"] is None
    assert "também é morador" not in client.get(f"/condominios/{condo.id}/proprietarios/").content.decode()


def test_resident_of_other_condominium_does_not_count(api_client, condo, other_condo, make_owner, make_apartment, make_resident):
    paulo = make_owner(condo, "Paulo", CPF_PAULO)
    make_resident(other_condo, make_apartment(other_condo, "9"), "Paulo", CPF_PAULO)

    assert api_client.get(f"/api/condominios/{condo.id}/proprietarios/{paulo.id}/").json()["resident_of"] is None
