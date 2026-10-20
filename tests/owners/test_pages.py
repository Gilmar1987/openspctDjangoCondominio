import uuid

import pytest

from apartments.models import ApartmentRecord
from owners.models import OwnerRecord
from tests.conftest import CPF_ANA, CPF_MARIA, CPF_PAULO

pytestmark = pytest.mark.django_db


def base(condo):
    return f"/condominios/{condo.id}/proprietarios/"


def owner_of(apartment):
    return ApartmentRecord.objects.get(id=apartment.id).owner_id


def test_list_page_masks_cpf_and_shows_count(client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo", CPF_PAULO, phone="81999990000")
    make_owner(condo, "Ana", CPF_ANA)
    make_apartment(condo, "101", owner=paulo)

    content = client.get(base(condo)).content.decode()

    assert content.index("Ana") < content.index("Paulo")
    assert "***.444.777-**" in content and "(81) 99999-0000" in content
    assert CPF_PAULO not in content and "111.444.777-35" not in content


def test_list_page_empty(client, condo):
    assert "Nenhum proprietário cadastrado" in client.get(base(condo)).content.decode()


def test_detail_page_shows_apartments_with_masked_cpf(client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo")
    make_apartment(condo, "101", tower="A", owner=paulo)

    content = client.get(f"{base(condo)}{paulo.id}/").content.decode()

    assert "Torre A · Nº 101" in content and "***.444.777-**" in content
    assert CPF_PAULO not in content


def test_create_form_offers_only_free_apartments(client, condo, make_owner, make_apartment):
    ana = make_owner(condo, "Ana", CPF_ANA)
    free = make_apartment(condo, "101")
    taken = make_apartment(condo, "102", owner=ana)

    content = client.get(f"{base(condo)}novo/").content.decode()

    assert f'value="{free.id}"' in content and f'value="{taken.id}"' not in content


def test_edit_form_offers_free_and_own_and_full_cpf(client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo")
    ana = make_owner(condo, "Ana", CPF_ANA)
    free, own = make_apartment(condo, "101"), make_apartment(condo, "102", owner=paulo)
    taken = make_apartment(condo, "103", owner=ana)

    content = client.get(f"{base(condo)}{paulo.id}/editar/").content.decode()

    assert f'value="{free.id}"' in content and f'value="{own.id}" checked' in content
    assert f'value="{taken.id}"' not in content
    assert f'value="{CPF_PAULO}"' in content


def test_create_page_links_apartments(client, condo, make_apartment):
    x, y = make_apartment(condo, "101"), make_apartment(condo, "102")

    response = client.post(f"{base(condo)}novo/", {"name": "Paulo", "cpf": "111.444.777-35", "apartment_ids": [str(x.id), str(y.id)]})

    owner = OwnerRecord.objects.get()
    assert response.status_code == 302
    assert (owner_of(x), owner_of(y)) == (owner.id, owner.id)


def test_form_error_keeps_values_and_shows_message_at_cpf(client, condo, make_apartment):
    x = make_apartment(condo, "101")

    response = client.post(
        f"{base(condo)}novo/",
        {"name": "Maria Souza", "cpf": "529.982.247-26", "email": "maria@exemplo.com", "apartment_ids": [str(x.id)]},
    )

    content = response.content.decode()
    cpf_field = content[content.index('id="cpf"'):]
    assert response.status_code == 200
    assert 'value="Maria Souza"' in content and 'value="maria@exemplo.com"' in content
    assert f'value="{x.id}" checked' in content
    assert cpf_field.index("O CPF informado é inválido.") < cpf_field.index("</div>")
    assert OwnerRecord.objects.count() == 0


def test_link_error_is_shown(client, condo, make_owner, make_apartment):
    ana = make_owner(condo, "Ana", CPF_ANA)
    taken = make_apartment(condo, "103", owner=ana)

    response = client.post(f"{base(condo)}novo/", {"name": "Paulo", "cpf": CPF_PAULO, "apartment_ids": [str(taken.id)]})

    assert "O apartamento Nº 103 já tem outro proprietário." in response.content.decode()
    assert owner_of(taken) == ana.id


def test_edit_page_updates_and_releases(client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo")
    x, y = make_apartment(condo, "101", owner=paulo), make_apartment(condo, "102", owner=paulo)

    response = client.post(f"{base(condo)}{paulo.id}/editar/", {"name": "Paulo", "cpf": CPF_PAULO, "phone": "8133334444", "apartment_ids": [str(x.id)]})

    assert response.status_code == 302
    assert OwnerRecord.objects.get(id=paulo.id).phone == "8133334444"
    assert (owner_of(x), owner_of(y)) == (paulo.id, None)


def test_delete_confirmation_shows_count_without_deleting(client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo")
    make_apartment(condo, "101", owner=paulo)
    make_apartment(condo, "102", owner=paulo)

    content = client.get(f"{base(condo)}{paulo.id}/excluir/").content.decode()

    assert "Confirmar exclusão" in content and "2 apartamentos ficarão sem proprietário" in content
    assert OwnerRecord.objects.filter(id=paulo.id).exists()


def test_delete_page_releases_apartments(client, condo, make_owner, make_apartment):
    paulo = make_owner(condo, "Paulo")
    x = make_apartment(condo, "101", owner=paulo)

    response = client.post(f"{base(condo)}{paulo.id}/excluir/")

    assert response.status_code == 302
    assert not OwnerRecord.objects.filter(id=paulo.id).exists()
    assert ApartmentRecord.objects.filter(id=x.id).exists() and owner_of(x) is None


def test_cross_tenant_and_unknown_pages_are_404(client, condo, other_condo, make_owner):
    foreign = make_owner(other_condo, "Bruno", CPF_MARIA)

    for path in ("", "editar/", "excluir/"):
        assert client.get(f"{base(condo)}{foreign.id}/{path}").status_code == 404
    assert client.post(f"{base(condo)}{foreign.id}/excluir/").status_code == 404
    assert client.get(f"/condominios/{uuid.uuid4()}/proprietarios/").status_code == 404
    assert OwnerRecord.objects.filter(id=foreign.id).exists()


def test_navigation_links_between_apartments_and_owners(client, condo):
    condominiums = client.get("/condominios/").content.decode()
    apartments = client.get(f"/condominios/{condo.id}/apartamentos/").content.decode()

    assert f'href="/condominios/{condo.id}/proprietarios/"' in condominiums
    assert f'href="/condominios/{condo.id}/proprietarios/"' in apartments
