from django.shortcuts import render
from django.views.decorators.http import require_GET
from rest_framework.response import Response

from condominiums import repository
from condominiums.domain import Condominium
from condominiums.features import as_json


def handle() -> list[Condominium]:
    return repository.list_all()


def api(request):
    return Response([as_json(c) for c in handle()])


@require_GET
def page(request):
    return render(request, "condominiums/list.html", {"condominiums": handle()})
