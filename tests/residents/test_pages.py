import uuid

import pytest

from residents.models import ResidentRecord
from tests.conftest import CPF_JOAO, CPF_MARIA, CPF_PAULO

pytestmark = pytest.mark.django_db


def base(condo):
    return f"/condominios/{condo.id}/moradores/"


@pytest.fixture
def a101(condo, make_apartment):
    return make_apartment(condo, "101", tower="A")


def test_list_page_alphabetical_masked_with_apartment(client, condo, make_apartment, a101, make_resident):
    make_resident(condo, make_apartment(condo, "202", tower="B"), "Maria", CPF_MARIA)
    make_resident(condo, a101, "João", CPF_JOAO)

    content = client.get(base(condo)).content.decode()

    assert content.index("João") < content.index("Maria")
    assert "Torre A · Nº 101" in content and "***.533.447-**" in content
    assert CPF_JOAO not in content


def test_list_page_empty(client, condo):
    assert "Nenhum morador cadastrado" in client.get(base(condo)).content.decode()


def test_list_and_detail_show_also_owner(client, condo, make_apartment, make_owner, make_resident):
    paulo = make_owner(condo, "Paulo", CPF_PAULO)
    apartment = make_apartment(condo, "101", owner=paulo)
    make_apartment(condo, "102", owner=paulo)
    resident = make_resident(condo, apartment, "Paulo", CPF_PAULO)

    listing = client.get(base(condo)).content.decode()
    detail = client.get(f"{base(condo)}{resident.id}/").content.decode()

    assert "também é proprietário (2 apartamentos)" in listing
    assert "também é proprietário (2 apartamentos)" in detail
    assert CPF_PAULO not in detail


def test_create_page(client, condo, a101):
    response = client.post(f"{base(condo)}novo/", {"name": "João", "cpf": "390.533.447-05", "apartment_id": str(a101.id)})

    assert response.status_code == 302
    assert ResidentRecord.objects.get().apartment_id == a101.id


def test_form_lists_condominium_apartments(client, condo, other_condo, make_apartment, a101):
    make_apartment(other_condo, "999")

    content = client.get(f"{base(condo)}novo/").content.decode()

    assert f'value="{a101.id}"' in content and "Torre A · Nº 101" in content
    assert "Nº 999" not in content


def test_prefill_from_owner_does_not_save(client, condo, make_owner, a101):
    paulo = make_owner(condo, "Paulo", CPF_PAULO, email="paulo@exemplo.com", phone="81999990000")

    content = client.get(f"{base(condo)}novo/?proprietario={paulo.id}").content.decode()

    assert 'value="Paulo"' in content and f'value="{CPF_PAULO}"' in content
    assert 'value="paulo@exemplo.com"' in content and 'value="81999990000"' in content
    assert ResidentRecord.objects.count() == 0


def test_prefill_ignores_owner_from_other_condominium(client, condo, other_condo, make_owner):
    foreign = make_owner(other_condo, "Bruno", CPF_PAULO)

    content = client.get(f"{base(condo)}novo/?proprietario={foreign.id}").content.decode()

    assert 'value="Bruno"' not in content and CPF_PAULO not in content


def test_form_error_keeps_values_and_shows_message_at_cpf(client, condo, a101):
    response = client.post(f"{base(condo)}novo/", {"name": "João Lima", "cpf": "390.533.447-06", "apartment_id": str(a101.id)})

    content = response.content.decode()
    cpf_field = content[content.index('id="cpf"'):]
    assert 'value="João Lima"' in content
    assert f'value="{a101.id}" selected' in content
    assert cpf_field.index("O CPF informado é inválido.") < cpf_field.index("</div>")


def test_edit_page_shows_full_cpf_and_moves(client, condo, make_apartment, a101, make_resident):
    joao = make_resident(condo, a101)
    b202 = make_apartment(condo, "202", tower="B")
    url = f"{base(condo)}{joao.id}/editar/"

    page = client.get(url).content.decode()
    response = client.post(url, {"name": "João", "cpf": CPF_JOAO, "apartment_id": str(b202.id)})

    assert f'value="{CPF_JOAO}"' in page and f'value="{a101.id}" selected' in page
    assert response.status_code == 302
    assert ResidentRecord.objects.get(id=joao.id).apartment_id == b202.id


def test_delete_requires_confirmation(client, condo, a101, make_resident):
    joao = make_resident(condo, a101)
    url = f"{base(condo)}{joao.id}/excluir/"

    confirm = client.get(url).content.decode()
    assert "Confirmar exclusão" in confirm and ResidentRecord.objects.filter(id=joao.id).exists()
    assert client.post(url).status_code == 302
    assert not ResidentRecord.objects.filter(id=joao.id).exists()


def test_cross_tenant_and_unknown_pages_are_404(client, condo, other_condo, make_apartment, make_resident):
    foreign = make_resident(other_condo, make_apartment(other_condo, "1"))

    for path in ("", "editar/", "excluir/"):
        assert client.get(f"{base(condo)}{foreign.id}/{path}").status_code == 404
    assert client.get(f"/condominios/{uuid.uuid4()}/moradores/").status_code == 404


def test_navigation_links(client, condo):
    condominiums = client.get("/condominios/").content.decode()
    apartments = client.get(f"/condominios/{condo.id}/apartamentos/").content.decode()
    owners = client.get(f"/condominios/{condo.id}/proprietarios/").content.decode()

    for content in (condominiums, apartments, owners):
        assert f'href="/condominios/{condo.id}/moradores/"' in content
