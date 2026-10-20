from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response

from apartments import public as apartments
from owners.domain import Owner
from owners.features import BUSINESS_ERRORS, business_errors, detail_json, form_options, log_rejected, save_owner
from owners.features.get_owner import handle as get_owner
from owners.inputs import OwnerInput, parse_owner
from shared.http import validation_error_response
from tenancy.public import TenantRef, get_condominium_or_404

TEMPLATE = "owners/form.html"


def handle(tenant: TenantRef, owner_id, data: OwnerInput) -> Owner:
    current = get_owner(tenant, owner_id)
    updated = current.update(name=data.name, cpf=data.cpf, email=data.email, phone=data.phone)
    return save_owner(tenant, updated, data.apartment_ids)


def api(request, condominium_id, owner_id):
    """PUT: substituição completa; o conjunto de apartamentos informado substitui o anterior."""
    tenant = get_condominium_or_404(condominium_id)
    get_owner(tenant, owner_id)
    data, errors = parse_owner(request.data)
    if not errors:
        try:
            owner = handle(tenant, owner_id, data)
        except BUSINESS_ERRORS as exc:
            errors = business_errors(exc)
        else:
            return Response(detail_json(tenant, owner))
    log_rejected(tenant, errors)
    return validation_error_response(errors)


@require_http_methods(["GET", "POST"])
def page(request, condominium_id, owner_id):
    tenant = get_condominium_or_404(condominium_id)
    current = get_owner(tenant, owner_id)
    context = {
        "tenant": tenant,
        "title": "Editar proprietário",
        # O formulário de edição é o único lugar das páginas que mostra o CPF completo.
        "values": {"name": current.name, "cpf": current.cpf, "email": current.email, "phone": current.phone},
        "errors": {},
        "options": form_options(tenant, current.id),
        "selected": {str(a.id) for a in apartments.list_by_owner(tenant.id, current.id)},
    }
    if request.method == "GET":
        return render(request, TEMPLATE, context)
    data, errors = parse_owner(request.POST)
    if not errors:
        try:
            owner = handle(tenant, owner_id, data)
        except BUSINESS_ERRORS as exc:
            errors = business_errors(exc)
        else:
            messages.success(request, f"Proprietário “{owner.name}” atualizado.")
            return redirect("owners:list", condominium_id=tenant.id)
    log_rejected(tenant, errors)
    selected = set(request.POST.getlist("apartment_ids"))
    return render(request, TEMPLATE, {**context, "values": request.POST, "errors": errors, "selected": selected})
