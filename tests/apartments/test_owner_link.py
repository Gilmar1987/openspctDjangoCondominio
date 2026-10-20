"""Cenários da delta de `apartamentos`: proprietário do apartamento e exibição dele."""

import uuid

import pytest

from apartments.domain import Apartment
from apartments.inputs import parse_apartment
from apartments.models import ApartmentRecord
from tests.conftest import CPF_ANA, CPF_MARIA

pytestmark = pytest.mark.django_db

NOT_FOUND = {"errors": {"owner_id": ["O proprietário não foi encontrado neste condomínio."]}}


def collection(condo):
    return f"/api/condominios/{condo.id}/apartamentos/"


def item(condo, apartment):
    return f"{collection(condo)}{apartment.id}/"


@pytest.fixture
def paulo(condo, make_owner):
    return make_owner(condo, "Paulo")


@pytest.fixture
def ana(condo, make_owner):
    return make_owner(condo, "Ana", CPF_ANA)


# Domínio e entrada


def test_domain_keeps_and_changes_owner():
    tenant, owner, other = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    apartment = Apartment.create(tenant, "301", owner_id=owner)

    assert apartment.owner_id == owner
    assert apartment.update(number="301", tower=None, block=None, floor=None, owner_id=other).owner_id == other
    assert apartment.update(number="301", tower=None, block=None, floor=None).owner_id is None


@pytest.mark.parametrize("value", ["", "  ", None])
def test_input_blank_owner_is_absent(value):
    data, errors = parse_apartment({"number": "1", "owner_id": value})

    assert errors is None and data.owner_id is None


def test_input_invalid_owner_uuid():
    _, errors = parse_apartment({"number": "1", "owner_id": "nao-e-uuid"})

    assert errors == NOT_FOUND["errors"]


# API


def test_create_with_owner(api_client, condo, paulo):
    response = api_client.post(collection(condo), {"number": "301", "owner_id": str(paulo.id)}, format="json")

    assert response.status_code == 201
    body = response.json()
    assert (body["owner_id"], body["owner_name"]) == (str(paulo.id), "Paulo")
    assert ApartmentRecord.objects.get(id=body["id"]).owner_id == paulo.id


def test_change_owner(api_client, condo, make_apartment, paulo, ana):
    apartment = make_apartment(condo, "101", owner=ana)

    response = api_client.put(item(condo, apartment), {"number": "101", "owner_id": str(paulo.id)}, format="json")

    assert response.status_code == 200
    assert response.json()["owner_name"] == "Paulo"
    assert not ApartmentRecord.objects.filter(owner_id=ana.id).exists()


def test_remove_owner(api_client, condo, make_apartment, paulo):
    apartment = make_apartment(condo, "101", owner=paulo)

    response = api_client.put(item(condo, apartment), {"number": "101", "owner_id": None}, format="json")

    assert response.status_code == 200
    assert (response.json()["owner_id"], response.json()["owner_name"]) == (None, None)
    apartment.refresh_from_db()
    assert apartment.owner_id is None


def test_owner_from_other_condominium_is_rejected(api_client, condo, other_condo, make_owner, make_apartment):
    foreign = make_owner(other_condo, "Bruno", CPF_MARIA)
    apartment = make_apartment(condo, "101")

    created = api_client.post(collection(condo), {"number": "102", "owner_id": str(foreign.id)}, format="json")
    updated = api_client.put(item(condo, apartment), {"number": "101", "owner_id": str(foreign.id)}, format="json")

    assert (created.status_code, created.json()) == (400, NOT_FOUND)
    assert (updated.status_code, updated.json()) == (400, NOT_FOUND)
    assert ApartmentRecord.objects.filter(number="102").count() == 0
    apartment.refresh_from_db()
    assert apartment.owner_id is None


def test_unknown_owner_is_rejected(api_client, condo):
    response = api_client.post(collection(condo), {"number": "1", "owner_id": str(uuid.uuid4())}, format="json")

    assert (response.status_code, response.json()) == (400, NOT_FOUND)
    assert ApartmentRecord.objects.count() == 0


def test_api_returns_owner_in_list_and_detail(api_client, condo, make_apartment, paulo):
    owned = make_apartment(condo, "101", owner=paulo)
    make_apartment(condo, "102")

    listed = api_client.get(collection(condo)).json()
    detail = api_client.get(item(condo, owned)).json()

    assert [(a["number"], a["owner_name"]) for a in listed] == [("101", "Paulo"), ("102", None)]
    assert (detail["owner_id"], detail["owner_name"]) == (str(paulo.id), "Paulo")


# Páginas


def test_list_page_shows_owner_or_dash(client, condo, make_apartment, paulo):
    make_apartment(condo, "101", owner=paulo)
    make_apartment(condo, "102")

    content = client.get(f"/condominios/{condo.id}/apartamentos/").content.decode()
    row_101 = content[content.index(">101<"):]
    row_102 = content[content.index(">102<"):]

    assert "Paulo" in row_101[: row_101.index("</tr>")]
    assert "<td>—</td>" in row_102[: row_102.index("</tr>")]


def test_form_offers_owners_alphabetically_without_cpf(client, condo, other_condo, make_owner, paulo, ana):
    make_owner(other_condo, "Zeca", CPF_MARIA)

    content = client.get(f"/condominios/{condo.id}/apartamentos/novo/").content.decode()
    select = content[content.index('name="owner_id"'):content.index("</select>")]

    assert select.index("Sem proprietário") < select.index("Ana") < select.index("Paulo")
    assert "Zeca" not in select
    assert CPF_ANA not in content and "123.456.789" not in content


def test_create_page_with_owner(client, condo, paulo):
    response = client.post(f"/condominios/{condo.id}/apartamentos/novo/", {"number": "301", "owner_id": str(paulo.id)})

    assert response.status_code == 302
    assert ApartmentRecord.objects.get().owner_id == paulo.id


def test_edit_page_preselects_owner_and_rejects_foreign(client, condo, other_condo, make_owner, make_apartment, paulo):
    apartment = make_apartment(condo, "101", owner=paulo)
    foreign = make_owner(other_condo, "Bruno", CPF_MARIA)
    url = f"/condominios/{condo.id}/apartamentos/{apartment.id}/editar/"

    page = client.get(url).content.decode()
    rejected = client.post(url, {"number": "101", "owner_id": str(foreign.id)})

    assert f'value="{paulo.id}" selected' in page
    assert "O proprietário não foi encontrado neste condomínio." in rejected.content.decode()
    apartment.refresh_from_db()
    assert apartment.owner_id == paulo.id
