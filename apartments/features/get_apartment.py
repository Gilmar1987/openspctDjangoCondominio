from django.http import Http404
from rest_framework.response import Response

from apartments import repository
from apartments.domain import Apartment
from apartments.features import as_json
from tenancy.public import TenantRef, get_condominium_or_404


def handle(tenant: TenantRef, apartment_id) -> Apartment:
    apartment = repository.get(tenant.id, apartment_id)
    if apartment is None:
        raise Http404
    return apartment


def api(request, condominium_id, apartment_id):
    tenant = get_condominium_or_404(condominium_id)
    return Response(as_json(handle(tenant, apartment_id)))
