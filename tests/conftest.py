import pytest
from rest_framework.test import APIClient

from tenancy.models import Condominium


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_condominium(db):
    def make(name="Residencial Aurora"):
        return Condominium.objects.create(name=name)

    return make
