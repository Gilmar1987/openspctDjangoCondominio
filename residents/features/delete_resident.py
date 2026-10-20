from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response

from residents import repository
from residents.features.get_resident import handle as get_resident
from tenancy.public import TenantRef, get_condominium_or_404


def handle(tenant: TenantRef, resident_id) -> None:
    """Exclui só o cadastro de morador; um cadastro de proprietário da mesma pessoa não muda."""
    if not repository.delete(tenant.id, resident_id):
        raise Http404


def api(request, condominium_id, resident_id):
    tenant = get_condominium_or_404(condominium_id)
    handle(tenant, resident_id)
    return Response(status=status.HTTP_204_NO_CONTENT)


@require_http_methods(["GET", "POST"])
def page(request, condominium_id, resident_id):
    """GET pede confirmação explícita; só o POST exclui."""
    tenant = get_condominium_or_404(condominium_id)
    if request.method == "GET":
        resident = get_resident(tenant, resident_id)
        return render(request, "residents/confirm_delete.html", {"tenant": tenant, "resident": resident})
    handle(tenant, resident_id)
    messages.success(request, "Morador excluído.")
    return redirect("residents:list", condominium_id=tenant.id)
