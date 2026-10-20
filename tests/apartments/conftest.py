import pytest

from apartments.models import ApartmentRecord


@pytest.fixture
def condo(make_condominium):
    return make_condominium("Aurora")


@pytest.fixture
def other_condo(make_condominium):
    return make_condominium("Solar")


@pytest.fixture
def make_apartment(db):
    def make(condominium, number, tower=None, block=None, floor=None):
        return ApartmentRecord.objects.create(
            tenant=condominium, number=number, tower=tower, block=block, floor=floor
        )

    return make
