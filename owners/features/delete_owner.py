from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response

from apartments import public as apartments
from owners import repository
from owners.features.get_owner import handle as get_owner
from tenancy.public import TenantRef, get_condominium_or_404


def handle(tenant: TenantRef, owner_id) -> None:
    """Exclui o proprietário; os apartamentos dele ficam sem proprietário (mesma transação)."""
    with transaction.atomic():
        get_owner(tenant, owner_id)
        apartments.release_owner(tenant.id, owner_id)
        if not repository.delete(tenant.id, owner_id):
            raise Http404


def api(request, condominium_id, owner_id):
    tenant = get_condominium_or_404(condominium_id)
    handle(tenant, owner_id)
    return Response(status=status.HTTP_204_NO_CONTENT)


@require_http_methods(["GET", "POST"])
def page(request, condominium_id, owner_id):
    """GET pede confirmação explícita e informa quantos apartamentos serão desvinculados."""
    tenant = get_condominium_or_404(condominium_id)
    if request.method == "GET":
        owner = get_owner(tenant, owner_id)
        count = len(apartments.list_by_owner(tenant.id, owner.id))
        return render(request, "owners/confirm_delete.html", {"tenant": tenant, "owner": owner, "count": count})
    handle(tenant, owner_id)
    messages.success(request, "Proprietário excluído.")
    return redirect("owners:list", condominium_id=tenant.id)
