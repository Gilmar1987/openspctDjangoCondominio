import uuid

import pytest

from tenancy.models import Condominium

pytestmark = pytest.mark.django_db

URL = "/api/condominios/"


def test_create_returns_201_with_uuid(api_client):
    response = api_client.post(URL, {"name": "Residencial Aurora"}, format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Residencial Aurora"
    assert Condominium.objects.filter(id=uuid.UUID(body["id"])).exists()


def test_create_strips_name(api_client):
    response = api_client.post(URL, {"name": "  Solar  "}, format="json")

    assert response.json()["name"] == "Solar"


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_name_is_rejected(api_client, name):
    response = api_client.post(URL, {"name": name}, format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {"name": ["O campo nome é obrigatório."]}}
    assert Condominium.objects.count() == 0


def test_name_over_limit_is_rejected(api_client):
    response = api_client.post(URL, {"name": "a" * 121}, format="json")

    assert response.status_code == 400
    assert response.json() == {
        "errors": {"name": ["O campo nome deve ter no máximo 120 caracteres."]}
    }


def test_non_object_body_is_rejected(api_client):
    response = api_client.post(URL, ["Solar"], format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {"name": ["O campo nome é obrigatório."]}}


def test_list_is_alphabetical(api_client, make_condominium):
    make_condominium("Solar")
    make_condominium("aurora")
    make_condominium("Bela Vista")

    response = api_client.get(URL)

    assert response.status_code == 200
    assert [c["name"] for c in response.json()] == ["aurora", "Bela Vista", "Solar"]


def test_get_existing(api_client, make_condominium):
    condominium = make_condominium("Solar")

    response = api_client.get(f"{URL}{condominium.id}/")

    assert response.status_code == 200
    assert response.json() == {"id": str(condominium.id), "name": "Solar"}


def test_get_unknown_returns_404(api_client):
    response = api_client.get(f"{URL}{uuid.uuid4()}/")

    assert response.status_code == 404
    assert response.json() == {"detail": "Não encontrado."}
