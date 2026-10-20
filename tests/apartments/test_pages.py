import uuid

import pytest

from apartments.models import ApartmentRecord

pytestmark = pytest.mark.django_db


def base(condominium_id):
    return f"/condominios/{condominium_id}/apartamentos/"


def test_list_page_is_ordered(client, condo, make_apartment):
    make_apartment(condo, "101", tower="B")
    make_apartment(condo, "201", tower="A")

    content = client.get(base(condo.id)).content.decode()

    assert content.index("201") < content.index("101")
    assert "Aurora" in content


def test_list_page_empty(client, condo):
    response = client.get(base(condo.id))

    assert response.status_code == 200
    assert "Nenhum apartamento cadastrado" in response.content.decode()


def test_list_page_does_not_mix_condominiums(client, condo, other_condo, make_apartment):
    make_apartment(other_condo, "777")

    assert "777" not in client.get(base(condo.id)).content.decode()


def test_unknown_condominium_page_is_404(client):
    assert client.get(base(uuid.uuid4())).status_code == 404
    assert client.get(f"{base(uuid.uuid4())}novo/").status_code == 404


def test_create_page(client, condo):
    response = client.post(
        f"{base(condo.id)}novo/", {"tower": "A", "block": "", "floor": "3", "number": "301"}
    )

    assert response.status_code == 302
    assert response["Location"] == base(condo.id)
    created = ApartmentRecord.objects.get()
    assert (created.tenant_id, created.tower, created.block, created.floor, created.number) == (
        condo.id, "A", None, 3, "301",
    )


def test_create_page_error_keeps_values_and_shows_message_at_field(client, condo):
    response = client.post(f"{base(condo.id)}novo/", {"tower": "Torre Norte", "floor": "2", "number": ""})

    content = response.content.decode()
    assert response.status_code == 200
    assert 'value="Torre Norte"' in content
    assert 'value="2"' in content
    number_field = content[content.index('id="number"'):]
    assert number_field.index("O campo número é obrigatório.") < number_field.index("</div>")
    assert ApartmentRecord.objects.count() == 0


def test_create_page_duplicate(client, condo, make_apartment):
    make_apartment(condo, "101", tower="A")

    response = client.post(f"{base(condo.id)}novo/", {"tower": "a", "number": "101"})

    assert response.status_code == 200
    assert "Este apartamento já existe neste condomínio." in response.content.decode()
    assert ApartmentRecord.objects.count() == 1


def test_same_validation_message_in_page_and_api(client, api_client, condo):
    page = client.post(f"{base(condo.id)}novo/", {"number": "", "floor": "terceiro"})
    api = api_client.post(
        f"/api/condominios/{condo.id}/apartamentos/", {"number": "", "floor": "terceiro"}, format="json"
    )

    content = page.content.decode()
    for messages in api.json()["errors"].values():
        assert messages[0] in content


def test_edit_page_shows_current_values(client, condo, make_apartment):
    apartment = make_apartment(condo, "301", tower="A", floor=3)

    content = client.get(f"{base(condo.id)}{apartment.id}/editar/").content.decode()

    assert 'value="301"' in content and 'value="A"' in content and 'value="3"' in content


def test_edit_page_updates(client, condo, make_apartment):
    apartment = make_apartment(condo, "301", floor=3)

    response = client.post(f"{base(condo.id)}{apartment.id}/editar/", {"number": "301", "floor": "4"})

    assert response.status_code == 302
    apartment.refresh_from_db()
    assert apartment.floor == 4


def test_edit_page_duplicate_keeps_apartment(client, condo, make_apartment):
    make_apartment(condo, "101")
    apartment = make_apartment(condo, "102")

    response = client.post(f"{base(condo.id)}{apartment.id}/editar/", {"number": "101"})

    assert "Este apartamento já existe neste condomínio." in response.content.decode()
    apartment.refresh_from_db()
    assert apartment.number == "102"


def test_delete_requires_confirmation(client, condo, make_apartment):
    apartment = make_apartment(condo, "301")

    response = client.get(f"{base(condo.id)}{apartment.id}/excluir/")

    assert response.status_code == 200
    assert "Confirmar exclusão" in response.content.decode()
    assert ApartmentRecord.objects.filter(id=apartment.id).exists()


def test_delete_after_confirmation(client, condo, make_apartment):
    apartment = make_apartment(condo, "301")

    response = client.post(f"{base(condo.id)}{apartment.id}/excluir/")

    assert response.status_code == 302
    assert not ApartmentRecord.objects.filter(id=apartment.id).exists()
    assert "301" not in client.get(base(condo.id)).content.decode()


def test_unknown_apartment_pages_are_404(client, condo):
    missing = uuid.uuid4()

    assert client.get(f"{base(condo.id)}{missing}/editar/").status_code == 404
    assert client.post(f"{base(condo.id)}{missing}/excluir/").status_code == 404


def test_cross_tenant_pages_are_404_and_change_nothing(client, condo, other_condo, make_apartment):
    foreign = make_apartment(other_condo, "101")

    edit = client.post(f"{base(condo.id)}{foreign.id}/editar/", {"number": "999"})
    delete = client.post(f"{base(condo.id)}{foreign.id}/excluir/")

    assert (edit.status_code, delete.status_code) == (404, 404)
    foreign.refresh_from_db()
    assert (foreign.number, foreign.tenant_id) == ("101", other_condo.id)
