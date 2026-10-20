from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response

from residents.domain import Resident
from residents.features import (
    BUSINESS_ERRORS,
    business_errors,
    detail_json,
    form_context,
    log_rejected,
    save_resident,
)
from residents.features.get_resident import handle as get_resident
from residents.inputs import ResidentInput, parse_resident
from shared.http import validation_error_response
from tenancy.public import TenantRef, get_condominium_or_404

TEMPLATE = "residents/form.html"


def handle(tenant: TenantRef, resident_id, data: ResidentInput) -> Resident:
    current = get_resident(tenant, resident_id)
    updated = current.update(
        name=data.name, cpf=data.cpf, email=data.email, phone=data.phone, apartment_id=data.apartment_id
    )
    return save_resident(tenant, updated)


def api(request, condominium_id, resident_id):
    """PUT: substituição completa (mudar de apartamento é uma edição)."""
    tenant = get_condominium_or_404(condominium_id)
    get_resident(tenant, resident_id)
    data, errors = parse_resident(request.data)
    if not errors:
        try:
            resident = handle(tenant, resident_id, data)
        except BUSINESS_ERRORS as exc:
            errors = business_errors(exc)
        else:
            return Response(detail_json(tenant, resident))
    log_rejected(tenant, errors)
    return validation_error_response(errors)


@require_http_methods(["GET", "POST"])
def page(request, condominium_id, resident_id):
    tenant = get_condominium_or_404(condominium_id)
    current = get_resident(tenant, resident_id)
    context = {
        "tenant": tenant,
        "title": "Editar morador",
        # O formulário de edição é o único lugar das páginas que mostra o CPF completo.
        "values": {
            "name": current.name,
            "cpf": current.cpf,
            "email": current.email,
            "phone": current.phone,
            "apartment_id": current.apartment_id,
        },
        "errors": {},
        **form_context(tenant),
    }
    if request.method == "GET":
        return render(request, TEMPLATE, context)
    data, errors = parse_resident(request.POST)
    if not errors:
        try:
            resident = handle(tenant, resident_id, data)
        except BUSINESS_ERRORS as exc:
            errors = business_errors(exc)
        else:
            messages.success(request, f"Morador “{resident.name}” atualizado.")
            return redirect("residents:list", condominium_id=tenant.id)
    log_rejected(tenant, errors)
    return render(request, TEMPLATE, {**context, "values": request.POST, "errors": errors})
