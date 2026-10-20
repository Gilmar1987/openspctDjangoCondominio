from django.shortcuts import render
from django.views.decorators.http import require_GET
from rest_framework.response import Response

from residents import repository
from residents.features import as_json, context_for, display
from tenancy.public import TenantRef, get_condominium_or_404


def handle(tenant: TenantRef):
    residents = repository.list_for_tenant(tenant.id)
    labels, also_owner = context_for(tenant, residents)
    return [(r, labels.get(r.apartment_id), also_owner.get(r.id)) for r in residents]


def api(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    return Response([as_json(r, label, owner) for r, label, owner in handle(tenant)])


@require_GET
def page(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    rows = [display(r, label, owner) for r, label, owner in handle(tenant)]
    return render(request, "residents/list.html", {"tenant": tenant, "rows": rows})
