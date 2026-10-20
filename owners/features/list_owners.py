from django.shortcuts import render
from django.views.decorators.http import require_GET
from rest_framework.response import Response

from apartments import public as apartments
from owners import repository
from owners.features import display, list_json
from tenancy.public import TenantRef, get_condominium_or_404


def handle(tenant: TenantRef):
    counts = apartments.count_by_owner(tenant.id)
    return [(owner, counts.get(owner.id, 0)) for owner in repository.list_for_tenant(tenant.id)]


def api(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    return Response([list_json(owner, count) for owner, count in handle(tenant)])


@require_GET
def page(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    rows = [(display(owner), count) for owner, count in handle(tenant)]
    return render(request, "owners/list.html", {"tenant": tenant, "rows": rows})
