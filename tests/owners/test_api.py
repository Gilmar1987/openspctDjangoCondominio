import logging
import uuid

import pytest

from apartments.models import ApartmentRecord
from owners.models import OwnerRecord
from tests.conftest import CPF_ANA, CPF_MARIA, CPF_PAULO

pytestmark = pytest.mark.django_db

NOT_FOUND = {"detail": "Não encontrado."}


def collection(condo):
    return f"/api/condominios/{condo.id}/proprietarios/"


def item(condo, owner):
    return f"{collection(condo)}{owner.id}/"


def owner_of(apartment):
    return ApartmentRecord.objects.get(id=apartment.id).owner_id


# Campos e validação


def test_create_with_all_fields(api_client, condo):
    payload = {"name": "Maria Souza", "cpf": "529.982.247-25", "email": "maria@exemplo.com", "phone": "(81) 99999-0000"}

    response = api_client.post(collection(condo), payload, format="json")

    assert response.status_code == 201
    body = response.json()
    assert (body["name"], body["cpf_masked"], body["email"], body["phone"]) == (
        "Maria Souza", "***.982.247-**", "maria@exemplo.com", "81999990000",
    )
    assert "cpf" not in body and CPF_MARIA not in response.content.decode()
    assert OwnerRecord.objects.get(id=body["id"]).get_cpf() == CPF_MARIA


def test_create_with_only_required_fields(api_client, condo):
    response = api_client.post(collection(condo), {"name": "Ana", "cpf": CPF_ANA}, format="json")

    assert response.status_code == 201
    assert (response.json()["email"], response.json()["phone"], response.json()["apartments"]) == (None, None, [])


def test_missing_name_and_cpf(api_client, condo):
    response = api_client.post(collection(condo), {}, format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {"name": ["O campo nome é obrigatório."], "cpf": ["O campo CPF é obrigatório."]}}


@pytest.mark.parametrize("field, value, message", [
    ("email", "maria@", "O e-mail informado é inválido."),
    ("phone", "1234", "O telefone deve ter DDD e 8 ou 9 dígitos."),
    ("cpf", "529.982.247-26", "O CPF informado é inválido."),
    ("cpf", "111.111.111-11", "O CPF informado é inválido."),
])
def test_invalid_fields(api_client, condo, field, value, message):
    payload = {"name": "Maria", "cpf": CPF_MARIA, field: value}

    response = api_client.post(collection(condo), payload, format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {field: [message]}}
    assert OwnerRecord.objects.count() == 0


# Unicidade do CPF


def test_duplicate_cpf_on_create_and_update(api_client, condo, make_owner):
    make_owner(condo, "Maria", CPF_MARIA)
    paulo = make_owner(condo, "Paulo", CPF_PAULO)
    duplicate = {"errors": {"cpf": ["Já existe proprietário com este CPF neste condomínio."]}}

    created = api_client.post(collection(condo), {"name": "Outra", "cpf": "529.982.247-25"}, format="json")
    updated = api_client.put(item(condo, paulo), {"name": "Paulo", "cpf": CPF_MARIA}, format="json")

    assert (created.status_code, created.json()) == (400, duplicate)
    assert (updated.status_code, updated.json()) == (400, duplicate)
    assert OwnerRecord.objects.get(id=paulo.id).get_cpf() == CPF_PAULO


def test_same_cpf_in_other_condominium(api_client, condo, other_condo, make_owner):
    make_owner(condo, "Maria", CPF_MARIA)

    response = api_client.post(collection(other_condo), {"name": "Maria", "cpf": CPF_MARIA}, format="json")

    assert response.status_code == 201


# Proteção do CPF e logs


def test_list_masks_cpf(api_client, condo, make_owner):
    make_owner(condo, "Maria", CPF_MARIA)

    response = api_client.get(collection(condo))

    content = response.content.decode()
    assert response.json()[0]["cpf_masked"] == "***.982.247-**"
    assert CPF_MARIA not in content and "529.982.247-25" not in content


def test_get_individual_returns_full_cpf(api_client, condo, make_owner):
    maria = make_owner(condo, "Maria", CPF_MARIA)

    body = api_client.get(item(condo, maria)).json()

    assert (body["cpf"], body["cpf_masked"]) == (CPF_MARIA, "***.982.247-**")


def test_rejected_creation_does_not_log_personal_data(api_client, condo, caplog):
    payload = {"name": "Maria Souza", "cpf": "529.982.247-26", "email": "maria@exemplo.com", "phone": "81999990000"}

    with caplog.at_level(logging.INFO):
        api_client.post(collection(condo), payload, format="json")

    assert any("owner rejected" in r.getMessage() for r in caplog.records)
    logged = " ".join(r.getMessage() for r in caplog.records)
    for value in ("Maria Souza", "529.982.247-26", "52998224726", "maria@exemplo.com", "81999990000"):
        assert value not in logged


# Listagem e consulta


def test_list_alphabetical_with_apartment_count(api_client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo", CPF_PAULO)
    make_owner(condo, "Ana", CPF_ANA)
    make_apartment(condo, "101", owner=paulo)
    make_apartment(condo, "102", owner=paulo)

    listed = api_client.get(collection(condo)).json()

    assert [(o["name"], o["apartment_count"]) for o in listed] == [("Ana", 0), ("Paulo", 2)]


def test_get_with_linked_apartments(api_client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo")
    a = make_apartment(condo, "101", tower="A", owner=paulo)
    b = make_apartment(condo, "202", tower="B", owner=paulo)

    body = api_client.get(item(condo, paulo)).json()

    assert body["apartments"] == [
        {"id": str(a.id), "label": "Torre A · Nº 101"},
        {"id": str(b.id), "label": "Torre B · Nº 202"},
    ]


def test_list_empty(api_client, condo):
    assert api_client.get(collection(condo)).json() == []


# Vínculo pelo proprietário


def test_create_linking_n_apartments(api_client, condo, make_apartment):
    x, y = make_apartment(condo, "101"), make_apartment(condo, "102")

    response = api_client.post(
        collection(condo), {"name": "Paulo", "cpf": CPF_PAULO, "apartment_ids": [str(x.id), str(y.id)]}, format="json"
    )

    owner_id = uuid.UUID(response.json()["id"])
    assert response.status_code == 201
    assert (owner_of(x), owner_of(y)) == (owner_id, owner_id)


def test_update_removing_apartment_from_set(api_client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo")
    x, y = make_apartment(condo, "101", owner=paulo), make_apartment(condo, "102", owner=paulo)

    response = api_client.put(item(condo, paulo), {"name": "Paulo", "cpf": CPF_PAULO, "apartment_ids": [str(x.id)]}, format="json")

    assert response.status_code == 200
    assert (owner_of(x), owner_of(y)) == (paulo.id, None)


def test_apartment_of_other_owner_is_rejected(api_client, condo, make_owner, make_apartment):
    ana = make_owner(condo, "Ana", CPF_ANA)
    paulo = make_owner(condo, "Paulo")
    z = make_apartment(condo, "103", tower="A", owner=ana)

    response = api_client.put(item(condo, paulo), {"name": "Paulo", "cpf": CPF_PAULO, "apartment_ids": [str(z.id)]}, format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {"apartment_ids": ["O apartamento Torre A · Nº 103 já tem outro proprietário."]}}
    assert owner_of(z) == ana.id


def test_apartment_of_other_condominium_or_unknown_is_rejected(api_client, condo, other_condo, make_apartment):
    foreign = make_apartment(other_condo, "101")
    message = {"errors": {"apartment_ids": ["O apartamento não foi encontrado neste condomínio."]}}

    for apartment_id in (foreign.id, uuid.uuid4()):
        response = api_client.post(
            collection(condo), {"name": "Paulo", "cpf": CPF_PAULO, "apartment_ids": [str(apartment_id)]}, format="json"
        )
        assert (response.status_code, response.json()) == (400, message)
    assert OwnerRecord.objects.count() == 0
    assert owner_of(foreign) is None


# Edição e exclusão


def test_update_keeps_linked_apartments(api_client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo")
    x = make_apartment(condo, "101", owner=paulo)

    response = api_client.put(
        item(condo, paulo),
        {"name": "Paulo", "cpf": CPF_PAULO, "phone": "8133334444", "apartment_ids": [str(x.id)]},
        format="json",
    )

    assert response.json()["phone"] == "8133334444"
    assert owner_of(x) == paulo.id


def test_delete_releases_apartments(api_client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo")
    x, y = make_apartment(condo, "101", owner=paulo), make_apartment(condo, "102", owner=paulo)

    response = api_client.delete(item(condo, paulo))

    assert response.status_code == 204
    assert not OwnerRecord.objects.filter(id=paulo.id).exists()
    assert (owner_of(x), owner_of(y)) == (None, None)


# Corrida no vínculo (D7)


def test_corrida_apartamento_tomado_desfaz_a_transacao(api_client, condo, make_owner, make_apartment, monkeypatch):
    from apartments import public as apartments_public

    ana = make_owner(condo, "Ana", CPF_ANA)
    contested = make_apartment(condo, "101", tower="A")
    real_get_many = apartments_public.get_many

    def stale_then_taken(tenant_id, ids):
        # A checagem vê o apartamento livre; logo depois, Ana o toma (outra requisição).
        snapshot = real_get_many(tenant_id, ids)
        ApartmentRecord.objects.filter(id=contested.id).update(owner_id=ana.id)
        return snapshot

    monkeypatch.setattr(apartments_public, "get_many", stale_then_taken)

    response = api_client.post(
        collection(condo), {"name": "Paulo", "cpf": CPF_PAULO, "apartment_ids": [str(contested.id)]}, format="json"
    )

    assert response.status_code == 400
    assert response.json() == {"errors": {"apartment_ids": ["O apartamento Torre A · Nº 101 já tem outro proprietário."]}}
    assert not OwnerRecord.objects.filter(cpf_hash=OwnerRecord.hash_cpf(CPF_PAULO)).exists()
    # A "outra requisição" simulada usa a mesma conexão do teste, então o rollback também a
    # desfaz; o que importa é que a unidade não ficou com o proprietário desfeito.
    assert owner_of(contested) in (None, ana.id)
    assert set(OwnerRecord.objects.values_list("id", flat=True)) == {ana.id}


# Isolamento


def test_cross_tenant_access_is_404(api_client, condo, other_condo, make_owner):
    foreign = make_owner(other_condo, "Bruno", CPF_MARIA)
    url = f"{collection(condo)}{foreign.id}/"

    responses = [
        api_client.get(url),
        api_client.put(url, {"name": "X", "cpf": CPF_MARIA}, format="json"),
        api_client.delete(url),
    ]

    assert [(r.status_code, r.json()) for r in responses] == [(404, NOT_FOUND)] * 3
    assert OwnerRecord.objects.get(id=foreign.id).name == "Bruno"


def test_unknown_condominium_is_404(api_client):
    assert api_client.get(f"/api/condominios/{uuid.uuid4()}/proprietarios/").status_code == 404
