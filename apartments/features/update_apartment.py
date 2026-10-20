from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response

from apartments import repository
from apartments.domain import Apartment, DuplicateApartmentError, ensure_unique
from apartments.features import as_json, duplicate_errors, form_values
from apartments.features.get_apartment import handle as get_apartment
from apartments.inputs import ApartmentInput, parse_apartment
from shared.http import validation_error_response
from tenancy.public import TenantRef, get_condominium_or_404

TEMPLATE = "apartments/form.html"


def handle(tenant: TenantRef, apartment_id, data: ApartmentInput) -> Apartment:
    current = get_apartment(tenant, apartment_id)
    updated = current.update(number=data.number, tower=data.tower, block=data.block, floor=data.floor)
    ensure_unique(updated, repository.find_same_key(updated))
    if repository.update(updated) is None:
        raise Http404
    return updated


def api(request, condominium_id, apartment_id):
    """PUT: substituição completa; campos omitidos ficam ausentes (D8)."""
    tenant = get_condominium_or_404(condominium_id)
    get_apartment(tenant, apartment_id)
    data, errors = parse_apartment(request.data)
    if errors:
        return validation_error_response(errors)
    try:
        apartment = handle(tenant, apartment_id, data)
    except DuplicateApartmentError as exc:
        return validation_error_response(duplicate_errors(exc))
    return Response(as_json(apartment))


@require_http_methods(["GET", "POST"])
def page(request, condominium_id, apartment_id):
    tenant = get_condominium_or_404(condominium_id)
    current = get_apartment(tenant, apartment_id)
    context = {"tenant": tenant, "title": "Editar apartamento", "values": form_values(current), "errors": {}}
    if request.method == "GET":
        return render(request, TEMPLATE, context)
    data, errors = parse_apartment(request.POST)
    if not errors:
        try:
            handle(tenant, apartment_id, data)
        except DuplicateApartmentError as exc:
            errors = duplicate_errors(exc)
        else:
            messages.success(request, "Apartamento atualizado.")
            return redirect("apartments:list", condominium_id=tenant.id)
    return render(request, TEMPLATE, {**context, "values": request.POST, "errors": errors})
