import logging
import uuid

import pytest

from owners.models import OwnerRecord
from residents.models import ResidentRecord
from tests.conftest import CPF_ANA, CPF_JOAO, CPF_MARIA, CPF_PAULO

pytestmark = pytest.mark.django_db

NOT_FOUND = {"detail": "Não encontrado."}
APT_NOT_FOUND = {"errors": {"apartment_id": ["O apartamento não foi encontrado neste condomínio."]}}


def collection(condo):
    return f"/api/condominios/{condo.id}/moradores/"


def item(condo, resident):
    return f"{collection(condo)}{resident.id}/"


@pytest.fixture
def a101(condo, make_apartment):
    return make_apartment(condo, "101", tower="A")


@pytest.fixture
def b202(condo, make_apartment):
    return make_apartment(condo, "202", tower="B")


def payload(apartment, name="João Lima", cpf="390.533.447-05", **extra):
    return {"name": name, "cpf": cpf, "apartment_id": str(apartment.id), **extra}


# Campos


def test_create_with_all_fields(api_client, condo, a101):
    response = api_client.post(
        collection(condo), payload(a101, email="joao@exemplo.com", phone="(81) 98888-1111"), format="json"
    )

    assert response.status_code == 201
    body = response.json()
    assert (body["name"], body["cpf_masked"], body["phone"], body["apartment"]) == (
        "João Lima", "***.533.447-**", "81988881111", {"id": str(a101.id), "label": "Torre A · Nº 101"},
    )
    assert "cpf" not in body and CPF_JOAO not in response.content.decode()
    assert ResidentRecord.objects.get(id=body["id"]).get_cpf() == CPF_JOAO


def test_required_fields(api_client, condo):
    response = api_client.post(collection(condo), {}, format="json")

    assert response.status_code == 400
    assert response.json()["errors"] == {
        "name": ["O campo nome é obrigatório."],
        "cpf": ["O campo CPF é obrigatório."],
        "apartment_id": ["O campo apartamento é obrigatório."],
    }


@pytest.mark.parametrize("field, value, message", [
    ("cpf", "390.533.447-06", "O CPF informado é inválido."),
    ("email", "joao@", "O e-mail informado é inválido."),
    ("phone", "1234", "O telefone deve ter DDD e 8 ou 9 dígitos."),
])
def test_invalid_fields(api_client, condo, a101, field, value, message):
    response = api_client.post(collection(condo), payload(a101, **{field: value}), format="json")

    assert (response.status_code, response.json()) == (400, {"errors": {field: [message]}})
    assert ResidentRecord.objects.count() == 0


# Apartamento de moradia


def test_many_residents_in_same_apartment(api_client, condo, a101, make_resident):
    make_resident(condo, a101, "João", CPF_JOAO)

    response = api_client.post(collection(condo), payload(a101, "Maria", CPF_MARIA), format="json")

    assert response.status_code == 201
    assert ResidentRecord.objects.filter(apartment_id=a101.id).count() == 2


def test_apartment_of_other_condominium_or_unknown(api_client, condo, other_condo, make_apartment):
    foreign = make_apartment(other_condo, "101")

    for apartment_id in (foreign.id, uuid.uuid4()):
        response = api_client.post(
            collection(condo), {"name": "João", "cpf": CPF_JOAO, "apartment_id": str(apartment_id)}, format="json"
        )
        assert (response.status_code, response.json()) == (400, APT_NOT_FOUND)
    assert ResidentRecord.objects.count() == 0


def test_moving_apartment(api_client, condo, a101, b202, make_resident):
    joao = make_resident(condo, a101)

    response = api_client.put(item(condo, joao), payload(b202, "João", CPF_JOAO), format="json")

    assert response.status_code == 200
    assert ResidentRecord.objects.get(id=joao.id).apartment_id == b202.id
    assert not ResidentRecord.objects.filter(apartment_id=a101.id).exists()


def test_owner_living_in_apartment_not_his(api_client, condo, make_apartment, make_owner, make_resident):
    paulo = make_owner(condo, "Paulo", CPF_PAULO)
    make_apartment(condo, "101", tower="A", owner=paulo)
    make_apartment(condo, "102", tower="A", owner=paulo)
    other_owner = make_owner(condo, "Ana", CPF_ANA)
    b305 = make_apartment(condo, "305", tower="B", owner=other_owner)

    response = api_client.post(collection(condo), payload(b305, "Paulo", CPF_PAULO), format="json")

    assert response.status_code == 201


# Um único apartamento por morador no condomínio


def test_same_person_in_another_apartment_is_rejected(api_client, condo, a101, b202, make_resident):
    make_resident(condo, a101, "João", CPF_JOAO)

    response = api_client.post(collection(condo), payload(b202, "João", CPF_JOAO), format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {"cpf": ["Já existe morador com este CPF neste condomínio."]}}


def test_same_cpf_in_other_condominium(api_client, condo, other_condo, a101, make_apartment, make_resident):
    make_resident(condo, a101)

    response = api_client.post(collection(other_condo), payload(make_apartment(other_condo, "1"), "João", CPF_JOAO), format="json")

    assert response.status_code == 201


# Proteção dos dados


def test_list_masks_cpf_and_get_returns_full(api_client, condo, a101, make_resident):
    joao = make_resident(condo, a101)

    listed = api_client.get(collection(condo))
    detail = api_client.get(item(condo, joao)).json()

    assert listed.json()[0]["cpf_masked"] == "***.533.447-**"
    assert CPF_JOAO not in listed.content.decode()
    assert detail["cpf"] == CPF_JOAO


def test_rejected_creation_does_not_log_personal_data(api_client, condo, a101, caplog):
    data = payload(a101, "João Lima", "390.533.447-06", email="joao@exemplo.com", phone="81988881111")

    with caplog.at_level(logging.INFO):
        api_client.post(collection(condo), data, format="json")

    logged = " ".join(r.getMessage() for r in caplog.records)
    assert "resident rejected" in logged
    for value in ("João Lima", "390.533.447-06", "39053344706", "joao@exemplo.com", "81988881111"):
        assert value not in logged


# Listagem e consulta


def test_list_alphabetical_with_apartment(api_client, condo, a101, b202, make_resident):
    make_resident(condo, b202, "Maria", CPF_MARIA)
    make_resident(condo, a101, "João", CPF_JOAO)

    listed = api_client.get(collection(condo)).json()

    assert [(r["name"], r["apartment"]["label"]) for r in listed] == [
        ("João", "Torre A · Nº 101"), ("Maria", "Torre B · Nº 202"),
    ]


def test_list_empty(api_client, condo):
    assert api_client.get(collection(condo)).json() == []


# Morador que também é proprietário


def test_resident_recognized_as_owner(api_client, condo, make_apartment, make_owner, make_resident):
    paulo = make_owner(condo, "Paulo", CPF_PAULO)
    a101 = make_apartment(condo, "101", tower="A", owner=paulo)
    make_apartment(condo, "102", tower="A", owner=paulo)
    resident = make_resident(condo, a101, "Paulo", CPF_PAULO)

    listed = api_client.get(collection(condo)).json()
    detail = api_client.get(item(condo, resident)).json()

    expected = {"owner_id": str(paulo.id), "apartment_count": 2}
    assert listed[0]["also_owner"] == expected and detail["also_owner"] == expected


def test_resident_without_owner_record(api_client, condo, a101, make_resident):
    joao = make_resident(condo, a101)

    assert api_client.get(item(condo, joao)).json()["also_owner"] is None


def test_owner_of_other_condominium_is_not_recognized(api_client, condo, other_condo, a101, make_owner, make_resident):
    make_owner(other_condo, "Paulo", CPF_PAULO)
    resident = make_resident(condo, a101, "Paulo", CPF_PAULO)

    assert api_client.get(item(condo, resident)).json()["also_owner"] is None


# Edição e exclusão


def test_update_keeps_apartment(api_client, condo, a101, make_resident):
    joao = make_resident(condo, a101)

    response = api_client.put(item(condo, joao), payload(a101, "João", CPF_JOAO, phone="8133334444"), format="json")

    assert response.json()["phone"] == "8133334444"
    assert ResidentRecord.objects.get(id=joao.id).apartment_id == a101.id


def test_delete_does_not_affect_owner_record(api_client, condo, make_apartment, make_owner, make_resident):
    paulo = make_owner(condo, "Paulo", CPF_PAULO)
    a101 = make_apartment(condo, "101", owner=paulo)
    resident = make_resident(condo, a101, "Paulo", CPF_PAULO)

    response = api_client.delete(item(condo, resident))

    assert response.status_code == 204
    assert not ResidentRecord.objects.filter(id=resident.id).exists()
    assert OwnerRecord.objects.filter(id=paulo.id).exists()


# Isolamento


def test_cross_tenant_is_404(api_client, condo, other_condo, make_apartment, make_resident):
    foreign = make_resident(other_condo, make_apartment(other_condo, "1"))
    url = f"{collection(condo)}{foreign.id}/"

    responses = [
        api_client.get(url),
        api_client.put(url, {"name": "X", "cpf": CPF_JOAO, "apartment_id": str(uuid.uuid4())}, format="json"),
        api_client.delete(url),
    ]

    assert [(r.status_code, r.json()) for r in responses] == [(404, NOT_FOUND)] * 3
    assert ResidentRecord.objects.get(id=foreign.id).name == "João"
