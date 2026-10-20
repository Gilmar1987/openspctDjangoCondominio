import uuid

import pytest
from django.db import connection

from owners import repository
from owners.domain import Owner
from owners.models import OwnerRecord
from people.domain import DuplicateCpfError
from tests.conftest import CPF_ANA, CPF_MARIA, CPF_PAULO

pytestmark = pytest.mark.django_db(transaction=True)


def add(condominium, name="Maria", cpf=CPF_MARIA, email=None, phone=None):
    return repository.add(Owner.create(condominium.id, name, cpf, email, phone))


def test_add_and_get_round_trip(condo):
    created = add(condo, email="maria@exemplo.com", phone="81999990000")

    assert isinstance(created.id, uuid.UUID)
    assert repository.get(condo.id, created.id) == created


def test_cpf_is_stored_only_encrypted(condo):
    created = add(condo)

    with connection.cursor() as cursor:
        cursor.execute("SELECT cpf_encrypted, cpf_hash FROM owner WHERE id = %s", [created.id])
        encrypted, digest = cursor.fetchone()
    assert CPF_MARIA not in encrypted and CPF_MARIA not in digest
    assert OwnerRecord.objects.get(id=created.id).get_cpf() == CPF_MARIA


def test_duplicate_cpf_in_same_condominium(condo):
    add(condo, name="Maria")

    with pytest.raises(DuplicateCpfError) as exc:
        add(condo, name="Outra", cpf="529.982.247-25")
    assert str(exc.value) == "Já existe proprietário com este CPF neste condomínio."


def test_update_to_duplicate_cpf_keeps_row(condo):
    add(condo, name="Maria")
    paulo = add(condo, name="Paulo", cpf=CPF_PAULO)

    with pytest.raises(DuplicateCpfError):
        repository.update(paulo.update(name="Paulo", cpf=CPF_MARIA, email=None, phone=None))
    assert repository.get(condo.id, paulo.id).cpf == CPF_PAULO


def test_same_cpf_in_other_condominium(condo, other_condo):
    add(condo)

    assert add(other_condo).tenant_id == other_condo.id


def test_list_is_alphabetical_and_isolated(condo, other_condo):
    add(condo, name="Paulo", cpf=CPF_PAULO)
    add(condo, name="ana", cpf=CPF_ANA)
    add(other_condo, name="Bruno")

    assert [o.name for o in repository.list_for_tenant(condo.id)] == ["ana", "Paulo"]


def test_get_update_delete_are_isolated_by_condominium(condo, other_condo):
    maria = add(condo)
    forged = Owner(id=maria.id, tenant_id=other_condo.id, name="X", cpf=CPF_PAULO, email=None, phone=None)

    assert repository.get(other_condo.id, maria.id) is None
    assert repository.update(forged) is None
    assert repository.delete(other_condo.id, maria.id) is False
    assert repository.get(condo.id, maria.id).name == "Maria"


def test_update_and_delete(condo):
    maria = add(condo)

    repository.update(maria.update(name="Maria", cpf=CPF_MARIA, email=None, phone="8133334444"))
    assert repository.get(condo.id, maria.id).phone == "8133334444"
    assert repository.delete(condo.id, maria.id) is True
    assert repository.get(condo.id, maria.id) is None
