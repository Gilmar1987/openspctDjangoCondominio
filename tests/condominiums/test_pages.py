import uuid

import pytest

from tenancy.models import Condominium

pytestmark = pytest.mark.django_db


def test_list_page_shows_condominiums_alphabetically(client, make_condominium):
    make_condominium("Solar")
    make_condominium("Aurora")

    response = client.get("/condominios/")

    content = response.content.decode()
    assert response.status_code == 200
    assert content.index("Aurora") < content.index("Solar")


def test_list_page_without_condominiums(client):
    response = client.get("/condominios/")

    assert "Nenhum condomínio cadastrado" in response.content.decode()


def test_create_page_creates_and_redirects_to_list(client):
    response = client.post("/condominios/novo/", {"name": "  Residencial Aurora "})

    assert response.status_code == 302
    assert response["Location"] == "/condominios/"
    assert Condominium.objects.get().name == "Residencial Aurora"


def test_create_page_redisplays_form_with_error(client):
    response = client.post("/condominios/novo/", {"name": "   "})

    content = response.content.decode()
    assert response.status_code == 200
    assert "O campo nome é obrigatório." in content
    assert Condominium.objects.count() == 0


def test_create_page_keeps_typed_value_on_error(client):
    response = client.post("/condominios/novo/", {"name": "a" * 121})

    content = response.content.decode()
    assert "O campo nome deve ter no máximo 120 caracteres." in content
    assert 'value="' + "a" * 121 + '"' in content


def test_same_validation_message_in_page_and_api(client, api_client):
    page = client.post("/condominios/novo/", {"name": ""})
    api = api_client.post("/api/condominios/", {"name": ""}, format="json")

    message = api.json()["errors"]["name"][0]
    assert api.status_code == 400
    assert message in page.content.decode()


def test_condominium_page_redirects_to_apartments(client, make_condominium):
    condominium = make_condominium()

    response = client.get(f"/condominios/{condominium.id}/")

    assert response.status_code == 302
    assert response["Location"] == f"/condominios/{condominium.id}/apartamentos/"


def test_condominium_page_unknown_returns_404(client):
    response = client.get(f"/condominios/{uuid.uuid4()}/")

    assert response.status_code == 404
