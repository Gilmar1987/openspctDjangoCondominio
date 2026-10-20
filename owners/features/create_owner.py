from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response

from owners.domain import Owner
from owners.features import BUSINESS_ERRORS, business_errors, detail_json, form_options, log_rejected, save_owner
from owners.inputs import OwnerInput, parse_owner
from shared.http import validation_error_response
from tenancy.public import TenantRef, get_condominium_or_404

TEMPLATE = "owners/form.html"


def handle(tenant: TenantRef, data: OwnerInput) -> Owner:
    owner = Owner.create(tenant.id, data.name, data.cpf, data.email, data.phone)
    return save_owner(tenant, owner, data.apartment_ids)


def api(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    data, errors = parse_owner(request.data)
    if not errors:
        try:
            owner = handle(tenant, data)
        except BUSINESS_ERRORS as exc:
            errors = business_errors(exc)
        else:
            return Response(detail_json(tenant, owner), status=status.HTTP_201_CREATED)
    log_rejected(tenant, errors)
    return validation_error_response(errors)


@require_http_methods(["GET", "POST"])
def page(request, condominium_id):
    tenant = get_condominium_or_404(condominium_id)
    context = {
        "tenant": tenant,
        "title": "Novo proprietário",
        "values": {},
        "errors": {},
        "options": form_options(tenant),
        "selected": set(),
    }
    if request.method == "GET":
        return render(request, TEMPLATE, context)
    data, errors = parse_owner(request.POST)
    if not errors:
        try:
            owner = handle(tenant, data)
        except BUSINESS_ERRORS as exc:
            errors = business_errors(exc)
        else:
            messages.success(request, f"Proprietário “{owner.name}” criado.")
            return redirect("owners:list", condominium_id=tenant.id)
    log_rejected(tenant, errors)
    selected = set(request.POST.getlist("apartment_ids"))
    return render(request, TEMPLATE, {**context, "values": request.POST, "errors": errors, "selected": selected})
