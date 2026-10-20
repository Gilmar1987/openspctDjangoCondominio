from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET
from rest_framework.response import Response

from residents import repository
from residents.domain import Resident
from residents.features import context_for, detail_json, display
from tenancy.public import TenantRef, get_condominium_or_404


def handle(tenant: TenantRef, resident_id) -> Resident:
    resident = repository.get(tenant.id, resident_id)
    if resident is None:
        raise Http404
    return resident


def api(request, condominium_id, resident_id):
    """Consulta individual: único ponto da API que devolve o CPF completo."""
    tenant = get_condominium_or_404(condominium_id)
    return Response(detail_json(tenant, handle(tenant, resident_id), include_cpf=True))


@require_GET
def page(request, condominium_id, resident_id):
    tenant = get_condominium_or_404(condominium_id)
    resident = handle(tenant, resident_id)
    labels, also_owner = context_for(tenant, [resident])
    data = display(resident, labels.get(resident.apartment_id), also_owner.get(resident.id))
    return render(request, "residents/detail.html", {"tenant": tenant, "resident": data})
