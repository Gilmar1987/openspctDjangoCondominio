"""Delta de `apartamentos` em cadastro-de-moradores: quantidade de moradores e bloqueio da exclusão."""

from unittest import mock

import pytest
from django.db.models import ProtectedError

from apartments.models import ApartmentRecord
from residents.models import ResidentRecord
from tests.conftest import CPF_JOAO, CPF_MARIA

pytestmark = pytest.mark.django_db

BLOCKED = "Este apartamento tem 2 moradores e precisa ficar sem moradores antes de ser excluído."


def api_item(condo, apartment):
    return f"/api/condominios/{condo.id}/apartamentos/{apartment.id}/"


@pytest.fixture
def two_residents(condo, make_apartment, make_resident):
    apartment = make_apartment(condo, "101", tower="A")
    make_resident(condo, apartment, "João", CPF_JOAO)
    make_resident(condo, apartment, "Maria", CPF_MARIA)
    return apartment


def test_resident_count_in_api_and_list(api_client, client, condo, make_apartment, two_residents):
    make_apartment(condo, "102", tower="A")

    listed = api_client.get(f"/api/condominios/{condo.id}/apartamentos/").json()
    detail = api_client.get(api_item(condo, two_residents)).json()
    page = client.get(f"/condominios/{condo.id}/apartamentos/").content.decode()

    assert [(a["number"], a["resident_count"]) for a in listed] == [("101", 2), ("102", 0)]
    assert detail["resident_count"] == 2
    assert "<th>Moradores</th>" in page
    row_101 = page[page.index(">101<"):]
    assert "<td>2</td>" in row_101[: row_101.index("</tr>")]


def test_api_delete_with_residents_is_blocked(api_client, condo, two_residents):
    response = api_client.delete(api_item(condo, two_residents))

    assert (response.status_code, response.json()) == (400, {"errors": {"apartment": [BLOCKED]}})
    assert ApartmentRecord.objects.filter(id=two_residents.id).exists()
    assert ResidentRecord.objects.count() == 2


def test_single_resident_message(api_client, condo, make_apartment, make_resident):
    apartment = make_apartment(condo, "101")
    make_resident(condo, apartment)

    response = api_client.delete(api_item(condo, apartment))

    assert response.json()["errors"]["apartment"] == [
        "Este apartamento tem 1 morador e precisa ficar sem moradores antes de ser excluído."
    ]


def test_page_confirmation_warns_and_hides_button(client, condo, two_residents):
    url = f"/condominios/{condo.id}/apartamentos/{two_residents.id}/excluir/"

    confirm = client.get(url).content.decode()
    posted = client.post(url)

    assert BLOCKED in confirm and 'class="danger"' not in confirm
    assert posted.status_code == 200 and BLOCKED in posted.content.decode()
    assert ApartmentRecord.objects.filter(id=two_residents.id).exists()


def test_protected_error_is_converted(api_client, condo, make_apartment):
    apartment = make_apartment(condo, "101")

    with mock.patch("apartments.repository.delete", side_effect=ProtectedError("protected", set())):
        response = api_client.delete(api_item(condo, apartment))

    assert response.status_code == 400
    assert "precisa ficar sem moradores" in response.json()["errors"]["apartment"][0]


def test_delete_without_residents_still_works(api_client, condo, make_apartment):
    apartment = make_apartment(condo, "101")

    assert api_client.delete(api_item(condo, apartment)).status_code == 204
    assert not ApartmentRecord.objects.filter(id=apartment.id).exists()
