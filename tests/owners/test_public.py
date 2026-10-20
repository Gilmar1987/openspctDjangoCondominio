import uuid

import pytest

from owners import public
from people.models import PersonModel
from tests.conftest import CPF_ANA, CPF_PAULO

pytestmark = pytest.mark.django_db


def test_owners_by_cpf_hash_is_restricted_to_condominium(condo, other_condo, make_owner):
    paulo = make_owner(condo, "Paulo", CPF_PAULO)
    make_owner(other_condo, "Ana", CPF_ANA)

    found = public.owners_by_cpf_hash(condo.id, [PersonModel.hash_cpf(CPF_PAULO), PersonModel.hash_cpf(CPF_ANA)])

    assert found == {PersonModel.hash_cpf(CPF_PAULO): public.OwnerRef(id=paulo.id, name="Paulo")}


def test_owners_by_cpf_hash_empty():
    assert public.owners_by_cpf_hash(uuid.uuid4(), []) == {}


def test_get_owner_person_for_prefill(condo, other_condo, make_owner):
    paulo = make_owner(condo, "Paulo", CPF_PAULO, email="paulo@exemplo.com", phone="81999990000")

    assert public.get_owner_person(condo.id, paulo.id) == public.OwnerPerson(
        name="Paulo", cpf=CPF_PAULO, email="paulo@exemplo.com", phone="81999990000"
    )
    assert public.get_owner_person(other_condo.id, paulo.id) is None
