from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET
from rest_framework.response import Response

from apartments import public as apartments
from owners import repository
from owners.domain import Owner
from owners.features import detail_json, display, residences
from tenancy.public import TenantRef, get_condominium_or_404


def handle(tenant: TenantRef, owner_id) -> Owner:
    owner = repository.get(tenant.id, owner_id)
    if owner is None:
        raise Http404
    return owner


def api(request, condominium_id, owner_id):
    """Consulta individual: único ponto da API que devolve o CPF completo."""
    tenant = get_condominium_or_404(condominium_id)
    return Response(detail_json(tenant, handle(tenant, owner_id), include_cpf=True))


@require_GET
def page(request, condominium_id, owner_id):
    tenant = get_condominium_or_404(condominium_id)
    owner = handle(tenant, owner_id)
    home = residences(tenant, [owner]).get(owner.id)
    return render(
        request,
        "owners/detail.html",
        {"tenant": tenant, "owner": display(owner, home), "apartments": apartments.list_by_owner(tenant.id, owner.id)},
    )
