from django.contrib import messages
from django.db.models import ProtectedError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response

from apartments import repository
from apartments.features import ApartmentHasResidentsError
from apartments.features.get_apartment import handle as get_apartment
from residents import public as residents
from shared.http import validation_error_response
from tenancy.public import TenantRef, get_condominium_or_404

TEMPLATE = "apartments/confirm_delete.html"


def handle(tenant: TenantRef, apartment_id) -> None:
    """Apartamento com moradores não é excluído (checagem aqui e PROTECT no banco)."""
    count = residents.count_in_apartment(tenant.id, apartment_id)
    if count:
        raise ApartmentHasResidentsError(count)
    try:
        deleted = repository.delete(tenant.id, apartment_id)
    except ProtectedError:
        raise ApartmentHasResidentsError(max(residents.count_in_apartment(tenant.id, apartment_id), 1))
    if not deleted:
        raise Http404


def api(request, condominium_id, apartment_id):
    tenant = get_condominium_or_404(condominium_id)
    try:
        handle(tenant, apartment_id)
    except ApartmentHasResidentsError as exc:
        return validation_error_response({"apartment": [str(exc)]})
    return Response(status=status.HTTP_204_NO_CONTENT)


@require_http_methods(["GET", "POST"])
def page(request, condominium_id, apartment_id):
    """GET pede confirmação explícita (ou avisa do bloqueio); só o POST exclui."""
    tenant = get_condominium_or_404(condominium_id)
    apartment = get_apartment(tenant, apartment_id)
    count = residents.count_in_apartment(tenant.id, apartment.id)
    context = {"tenant": tenant, "apartment": apartment, "blocked": str(ApartmentHasResidentsError(count)) if count else None}
    if request.method == "GET":
        return render(request, TEMPLATE, context)
    try:
        handle(tenant, apartment_id)
    except ApartmentHasResidentsError as exc:
        return render(request, TEMPLATE, {**context, "blocked": str(exc)})
    messages.success(request, "Apartamento excluído.")
    return redirect("apartments:list", condominium_id=tenant.id)
