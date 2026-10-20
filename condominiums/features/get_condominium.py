from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from rest_framework.response import Response

from condominiums import repository
from condominiums.domain import Condominium
from condominiums.features import as_json


def handle(condominium_id) -> Condominium:
    condominium = repository.get(condominium_id)
    if condominium is None:
        raise Http404
    return condominium


def api(request, condominium_id):
    return Response(as_json(handle(condominium_id)))


@require_GET
def page(request, condominium_id):
    handle(condominium_id)
    return redirect(f"/condominios/{condominium_id}/apartamentos/")
