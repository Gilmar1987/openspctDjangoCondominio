from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response

from apartments import repository
from apartments.domain import Apartment, DuplicateApartmentError, ensure_unique
from apartments.features import as_json, duplicate_errors
from apartments.inputs import ApartmentInput, parse_apartment
from shared.http import validation_error_response
from tenancy.public import TenantRef, get_condominium_or_404

TEMPLATE = "apartments/form.html"


def handle(tenant: TenantRef, data: ApartmentInput) -> Apartment:
    apartment = Apartment.create(tenant.id, data.number, data.tower, data.block, data.floor)
    ensure_unique(apartment, repository.find_same_key(apartment))
    return repository.add(apartment)


def api(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    data, errors = parse_apartment(request.data)
    if errors:
        return validation_error_response(errors)
    try:
        apartment = handle(tenant, data)
    except DuplicateApartmentError as exc:
        return validation_error_response(duplicate_errors(exc))
    return Response(as_json(apartment), status=status.HTTP_201_CREATED)


@require_http_methods(["GET", "POST"])
def page(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    context = {"tenant": tenant, "title": "Novo apartamento", "values": {}, "errors": {}}
    if request.method == "GET":
        return render(request, TEMPLATE, context)
    data, errors = parse_apartment(request.POST)
    if not errors:
        try:
            handle(tenant, data)
        except DuplicateApartmentError as exc:
            errors = duplicate_errors(exc)
        else:
            messages.success(request, "Apartamento criado.")
            return redirect("apartments:list", condominium_id=tenant.id)
    return render(request, TEMPLATE, {**context, "values": request.POST, "errors": errors})
