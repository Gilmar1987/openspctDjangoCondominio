import uuid

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response

from owners import public as owners
from residents.domain import Resident
from residents.features import (
    BUSINESS_ERRORS,
    business_errors,
    detail_json,
    form_context,
    log_rejected,
    save_resident,
)
from residents.inputs import ResidentInput, parse_resident
from shared.http import validation_error_response
from tenancy.public import TenantRef, get_condominium_or_404

TEMPLATE = "residents/form.html"


def handle(tenant: TenantRef, data: ResidentInput) -> Resident:
    resident = Resident.create(tenant.id, data.name, data.cpf, data.email, data.phone, apartment_id=data.apartment_id)
    return save_resident(tenant, resident)


def api(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    data, errors = parse_resident(request.data)
    if not errors:
        try:
            resident = handle(tenant, data)
        except BUSINESS_ERRORS as exc:
            errors = business_errors(exc)
        else:
            return Response(detail_json(tenant, resident), status=status.HTTP_201_CREATED)
    log_rejected(tenant, errors)
    return validation_error_response(errors)


def _prefill(tenant: TenantRef, owner_param: str) -> dict:
    """Pré-preenche a partir de um proprietário do mesmo condomínio; não grava nada (ADR-0017)."""
    try:
        owner_id = uuid.UUID(owner_param)
    except ValueError:
        return {}
    person = owners.get_owner_person(tenant.id, owner_id)
    if person is None:
        return {}
    return {"name": person.name, "cpf": person.cpf, "email": person.email, "phone": person.phone}


@require_http_methods(["GET", "POST"])
def page(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    context = {"tenant": tenant, "title": "Novo morador", "values": {}, "errors": {}, "creating": True, **form_context(tenant)}
    if request.method == "GET":
        owner_param = request.GET.get("proprietario", "")
        return render(request, TEMPLATE, {**context, "values": _prefill(tenant, owner_param), "prefill_owner": owner_param})
    data, errors = parse_resident(request.POST)
    if not errors:
        try:
            resident = handle(tenant, data)
        except BUSINESS_ERRORS as exc:
            errors = business_errors(exc)
        else:
            messages.success(request, f"Morador “{resident.name}” criado.")
            return redirect("residents:list", condominium_id=tenant.id)
    log_rejected(tenant, errors)
    return render(request, TEMPLATE, {**context, "values": request.POST, "errors": errors})
