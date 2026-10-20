from django.shortcuts import render
from django.views.decorators.http import require_GET
from rest_framework.response import Response

from apartments import repository
from apartments.domain import Apartment
from apartments.features import as_json, owner_names
from residents import public as residents
from tenancy.public import TenantRef, get_condominium_or_404


def handle(tenant: TenantRef) -> list[Apartment]:
    return repository.list_for_tenant(tenant.id)


def api(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    apartments = handle(tenant)
    names = owner_names(tenant, apartments)
    counts = residents.count_by_apartment(tenant.id)
    return Response([as_json(a, names.get(a.owner_id), counts.get(a.id, 0)) for a in apartments])


@require_GET
def page(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    apartments = handle(tenant)
    names = owner_names(tenant, apartments)
    counts = residents.count_by_apartment(tenant.id)
    rows = [(a, names.get(a.owner_id), counts.get(a.id, 0)) for a in apartments]
    return render(request, "apartments/list.html", {"tenant": tenant, "rows": rows})
