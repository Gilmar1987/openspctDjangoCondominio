import pytest
from rest_framework.test import APIClient

from apartments.models import ApartmentRecord
from owners import repository as owner_repository
from owners.domain import Owner
from tenancy.models import Condominium

# CPFs válidos usados nos testes (nunca dados reais).
CPF_MARIA = "52998224725"
CPF_PAULO = "11144477735"
CPF_ANA = "12345678909"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_condominium(db):
    def make(name="Residencial Aurora"):
        return Condominium.objects.create(name=name)

    return make


@pytest.fixture
def condo(make_condominium):
    return make_condominium("Aurora")


@pytest.fixture
def other_condo(make_condominium):
    return make_condominium("Solar")


@pytest.fixture
def make_apartment(db):
    def make(condominium, number, tower=None, block=None, floor=None, owner=None):
        return ApartmentRecord.objects.create(
            tenant=condominium,
            number=number,
            tower=tower,
            block=block,
            floor=floor,
            owner_id=owner.id if owner is not None else None,
        )

    return make


@pytest.fixture
def make_owner(db):
    def make(condominium, name="Paulo", cpf=CPF_PAULO, email=None, phone=None):
        return owner_repository.add(Owner.create(condominium.id, name, cpf, email, phone))

    return make


CPF_JOAO = "39053344705"


@pytest.fixture
def make_resident(db):
    from residents import repository as resident_repository
    from residents.domain import Resident

    def make(condominium, apartment, name="João", cpf=CPF_JOAO, email=None, phone=None):
        return resident_repository.add(
            Resident.create(condominium.id, name, cpf, email, phone, apartment_id=apartment.id)
        )

    return make
