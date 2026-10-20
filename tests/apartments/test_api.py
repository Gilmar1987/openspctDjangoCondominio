import uuid

import pytest

from apartments.models import ApartmentRecord

pytestmark = pytest.mark.django_db

DUPLICATE = {"errors": {"apartment": ["Este apartamento já existe neste condomínio."]}}
NOT_FOUND = {"detail": "Não encontrado."}


def collection(condominium_id):
    return f"/api/condominios/{condominium_id}/apartamentos/"


def item(condominium_id, apartment_id):
    return f"{collection(condominium_id)}{apartment_id}/"


# Criação e campos


def test_create_with_all_fields(api_client, condo):
    payload = {"tower": "A", "block": "1", "floor": 3, "number": "301"}

    response = api_client.post(collection(condo.id), payload, format="json")

    assert response.status_code == 201
    body = response.json()
    assert {k: body[k] for k in payload} == payload
    assert body["condominium_id"] == str(condo.id)
    assert ApartmentRecord.objects.get(id=body["id"]).tenant_id == condo.id


def test_create_with_only_number(api_client, condo):
    response = api_client.post(collection(condo.id), {"number": "12"}, format="json")

    assert response.status_code == 201
    body = response.json()
    assert (body["tower"], body["block"], body["floor"], body["number"]) == (None, None, None, "12")


def test_create_without_number(api_client, condo):
    response = api_client.post(collection(condo.id), {"tower": "A"}, format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {"number": ["O campo número é obrigatório."]}}
    assert ApartmentRecord.objects.count() == 0


@pytest.mark.parametrize("floor", [201, -6, "terceiro"])
def test_create_with_invalid_floor(api_client, condo, floor):
    response = api_client.post(collection(condo.id), {"number": "1", "floor": floor}, format="json")

    assert response.status_code == 400
    assert response.json() == {
        "errors": {"floor": ["O andar deve ser um número inteiro entre -5 e 200."]}
    }


def test_create_with_text_over_limit(api_client, condo):
    response = api_client.post(
        collection(condo.id), {"number": "1" * 11, "tower": "t" * 21}, format="json"
    )

    assert response.status_code == 400
    assert response.json()["errors"] == {
        "number": ["O campo número deve ter no máximo 10 caracteres."],
        "tower": ["O campo torre deve ter no máximo 20 caracteres."],
    }


def test_create_in_unknown_condominium(api_client):
    response = api_client.post(collection(uuid.uuid4()), {"number": "1"}, format="json")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND
    assert ApartmentRecord.objects.count() == 0


# Unicidade


def test_create_duplicate_in_same_condominium(api_client, condo, make_apartment):
    make_apartment(condo, "101", tower="A")

    response = api_client.post(collection(condo.id), {"tower": "a", "number": "101"}, format="json")

    assert response.status_code == 400
    assert response.json() == DUPLICATE
    assert ApartmentRecord.objects.count() == 1


def test_same_number_in_other_tower(api_client, condo, make_apartment):
    make_apartment(condo, "101", tower="A")

    response = api_client.post(collection(condo.id), {"tower": "B", "number": "101"}, format="json")

    assert response.status_code == 201


def test_same_apartment_in_other_condominium(api_client, condo, other_condo, make_apartment):
    make_apartment(condo, "101", tower="A")

    response = api_client.post(
        collection(other_condo.id), {"tower": "A", "number": "101"}, format="json"
    )

    assert response.status_code == 201


def test_update_to_duplicate_is_rejected(api_client, condo, make_apartment):
    make_apartment(condo, "101", tower="A")
    target = make_apartment(condo, "102", tower="A", floor=1)

    response = api_client.put(item(condo.id, target.id), {"tower": "A", "number": "101"}, format="json")

    assert response.status_code == 400
    assert response.json() == DUPLICATE
    target.refresh_from_db()
    assert (target.number, target.floor) == ("102", 1)


# Listagem e consulta


def test_list_is_ordered(api_client, condo, make_apartment):
    make_apartment(condo, "101", tower="B")
    make_apartment(condo, "201", tower="A")

    response = api_client.get(collection(condo.id))

    assert response.status_code == 200
    assert [(a["tower"], a["number"]) for a in response.json()] == [("A", "201"), ("B", "101")]


def test_list_empty(api_client, condo):
    response = api_client.get(collection(condo.id))

    assert response.status_code == 200
    assert response.json() == []


def test_get_apartment(api_client, condo, make_apartment):
    apartment = make_apartment(condo, "301", tower="A", floor=3)

    response = api_client.get(item(condo.id, apartment.id))

    assert response.status_code == 200
    assert response.json() == {
        "id": str(apartment.id),
        "condominium_id": str(condo.id),
        "tower": "A",
        "block": None,
        "floor": 3,
        "number": "301",
    }


def test_get_unknown_apartment(api_client, condo):
    response = api_client.get(item(condo.id, uuid.uuid4()))

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


# Edição


def test_update_floor(api_client, condo, make_apartment):
    apartment = make_apartment(condo, "301", floor=3)

    response = api_client.put(item(condo.id, apartment.id), {"number": "301", "floor": 4}, format="json")

    assert response.status_code == 200
    assert response.json()["floor"] == 4
    apartment.refresh_from_db()
    assert apartment.floor == 4


def test_update_ignores_condominium_in_body(api_client, condo, other_condo, make_apartment):
    apartment = make_apartment(condo, "301")

    response = api_client.put(
        item(condo.id, apartment.id),
        {"number": "301", "tenant": str(other_condo.id), "condominium_id": str(other_condo.id)},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["condominium_id"] == str(condo.id)
    apartment.refresh_from_db()
    assert apartment.tenant_id == condo.id


def test_update_with_invalid_data(api_client, condo, make_apartment):
    apartment = make_apartment(condo, "301")

    response = api_client.put(item(condo.id, apartment.id), {"number": " "}, format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {"number": ["O campo número é obrigatório."]}}


def test_update_unknown_apartment(api_client, condo):
    response = api_client.put(item(condo.id, uuid.uuid4()), {"number": "1"}, format="json")

    assert response.status_code == 404


# Exclusão


def test_delete(api_client, condo, make_apartment):
    apartment = make_apartment(condo, "301")

    response = api_client.delete(item(condo.id, apartment.id))

    assert response.status_code == 204
    assert api_client.get(collection(condo.id)).json() == []


def test_delete_unknown(api_client, condo, make_apartment):
    make_apartment(condo, "301")

    response = api_client.delete(item(condo.id, uuid.uuid4()))

    assert response.status_code == 404
    assert ApartmentRecord.objects.count() == 1


# Isolamento entre condomínios


def test_cross_tenant_get_is_404(api_client, condo, other_condo, make_apartment):
    foreign = make_apartment(other_condo, "101")

    response = api_client.get(item(condo.id, foreign.id))

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_cross_tenant_update_and_delete_are_404(api_client, condo, other_condo, make_apartment):
    foreign = make_apartment(other_condo, "101", floor=1)

    put = api_client.put(item(condo.id, foreign.id), {"number": "999"}, format="json")
    delete = api_client.delete(item(condo.id, foreign.id))

    assert (put.status_code, delete.status_code) == (404, 404)
    foreign.refresh_from_db()
    assert (foreign.number, foreign.floor, foreign.tenant_id) == ("101", 1, other_condo.id)


def test_list_does_not_mix_condominiums(api_client, condo, other_condo, make_apartment):
    make_apartment(condo, "101")
    make_apartment(other_condo, "202")

    response = api_client.get(collection(condo.id))

    assert [a["number"] for a in response.json()] == ["101"]
