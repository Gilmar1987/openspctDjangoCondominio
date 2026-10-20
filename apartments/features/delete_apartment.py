from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response

from apartments import repository
from apartments.features.get_apartment import handle as get_apartment
from tenancy.public import TenantRef, get_condominium_or_404


def handle(tenant: TenantRef, apartment_id) -> None:
    if not repository.delete(tenant.id, apartment_id):
        raise Http404


def api(request, condominium_id, apartment_id):
    tenant = get_condominium_or_404(condominium_id)
    handle(tenant, apartment_id)
    return Response(status=status.HTTP_204_NO_CONTENT)


@require_http_methods(["GET", "POST"])
def page(request, condominium_id, apartment_id):
    """GET pede confirmação explícita; só o POST exclui."""
    tenant = get_condominium_or_404(condominium_id)
    if request.method == "GET":
        apartment = get_apartment(tenant, apartment_id)
        return render(request, "apartments/confirm_delete.html", {"tenant": tenant, "apartment": apartment})
    handle(tenant, apartment_id)
    messages.success(request, "Apartamento excluído.")
    return redirect("apartments:list", condominium_id=tenant.id)
