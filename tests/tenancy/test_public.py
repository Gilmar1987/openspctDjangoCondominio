import uuid
from unittest import mock

import pytest
from django.http import Http404

from tenancy.models import Condominium, TenantQuerySet
from tenancy.public import TenantRef, get_condominium_or_404


@pytest.mark.django_db
def test_get_condominium_returns_existing_tenant():
    condominium = Condominium.objects.create(name="Residencial Aurora")

    tenant = get_condominium_or_404(condominium.id)

    assert tenant == TenantRef(id=condominium.id, name="Residencial Aurora")


@pytest.mark.django_db
def test_get_condominium_raises_404_for_unknown_id():
    with pytest.raises(Http404):
        get_condominium_or_404(uuid.uuid4())


@pytest.mark.django_db
def test_condominium_ids_are_uuids():
    condominium = Condominium.objects.create(name="Solar")

    assert isinstance(condominium.id, uuid.UUID)


def test_for_tenant_filters_by_tenant_id():
    tenant_id = uuid.uuid4()
    queryset = TenantQuerySet()

    with mock.patch.object(TenantQuerySet, "filter") as filter_:
        queryset.for_tenant(tenant_id)

    filter_.assert_called_once_with(tenant_id=tenant_id)
