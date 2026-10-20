import pytest
from django.db import connection

from people.models import PersonModel
from residents import public, repository
from residents.domain import Resident
from people.domain import DuplicateCpfError
from tests.conftest import CPF_JOAO, CPF_MARIA

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def apt(condo, make_apartment):
    return make_apartment(condo, "101", tower="A")


def add(condo, apartment, name="João", cpf=CPF_JOAO):
    return repository.add(Resident.create(condo.id, name, cpf, apartment_id=apartment.id))


def test_round_trip_and_cpf_only_encrypted(condo, apt):
    created = add(condo, apt)

    with connection.cursor() as cursor:
        cursor.execute("SELECT cpf_encrypted, cpf_hash FROM resident WHERE id = %s", [created.id])
        encrypted, digest = cursor.fetchone()
    assert CPF_JOAO not in encrypted and CPF_JOAO not in digest
    assert repository.get(condo.id, created.id) == created


def test_same_cpf_in_same_condominium_is_rejected(condo, apt, make_apartment):
    add(condo, apt)
    other = make_apartment(condo, "202", tower="B")

    with pytest.raises(DuplicateCpfError) as exc:
        add(condo, other, name="Outro")
    assert str(exc.value) == "Já existe morador com este CPF neste condomínio."


def test_same_cpf_in_other_condominium(condo, other_condo, apt, make_apartment):
    add(condo, apt)

    assert add(other_condo, make_apartment(other_condo, "101")).tenant_id == other_condo.id


def test_list_alphabetical_and_isolated(condo, other_condo, apt, make_apartment):
    add(condo, apt, "Maria", CPF_MARIA)
    add(condo, apt, "joão", CPF_JOAO)
    add(other_condo, make_apartment(other_condo, "1"), "Zeca", CPF_JOAO)

    assert [r.name for r in repository.list_for_tenant(condo.id)] == ["joão", "Maria"]


def test_update_moves_and_delete(condo, apt, make_apartment):
    joao = add(condo, apt)
    other = make_apartment(condo, "202")

    repository.update(joao.update(name="João", cpf=CPF_JOAO, email=None, phone=None, apartment_id=other.id))
    assert repository.get(condo.id, joao.id).apartment_id == other.id
    assert repository.delete(condo.id, joao.id) is True
    assert repository.get(condo.id, joao.id) is None


def test_public_counts_and_residences_by_hash(condo, other_condo, apt, make_apartment):
    empty = make_apartment(condo, "102")
    add(condo, apt, "João", CPF_JOAO)
    add(condo, apt, "Maria", CPF_MARIA)
    add(other_condo, make_apartment(other_condo, "9"), "João", CPF_JOAO)

    assert public.count_by_apartment(condo.id) == {apt.id: 2}
    assert (public.count_in_apartment(condo.id, apt.id), public.count_in_apartment(condo.id, empty.id)) == (2, 0)
    hashes = [PersonModel.hash_cpf(CPF_JOAO), PersonModel.hash_cpf("12345678909")]
    assert public.residences_by_cpf_hash(condo.id, hashes) == {PersonModel.hash_cpf(CPF_JOAO): apt.id}
