from django.shortcuts import render
from django.views.decorators.http import require_GET
from rest_framework.response import Response

from apartments import repository
from apartments.domain import Apartment
from apartments.features import as_json
from tenancy.public import TenantRef, get_condominium_or_404


def handle(tenant: TenantRef) -> list[Apartment]:
    return repository.list_for_tenant(tenant.id)


def api(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    return Response([as_json(a) for a in handle(tenant)])


@require_GET
def page(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    return render(request, "apartments/list.html", {"tenant": tenant, "apartments": handle(tenant)})
