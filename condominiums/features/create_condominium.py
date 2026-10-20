from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response

from condominiums import repository
from condominiums.domain import Condominium
from condominiums.features import as_json
from condominiums.inputs import CondominiumInput, parse_condominium
from shared.http import validation_error_response

TEMPLATE = "condominiums/form.html"


def handle(data: CondominiumInput) -> Condominium:
    return repository.add(Condominium.create(data.name))


def api(request):
    data, errors = parse_condominium(request.data)
    if errors:
        return validation_error_response(errors)
    return Response(as_json(handle(data)), status=status.HTTP_201_CREATED)


@require_http_methods(["GET", "POST"])
def page(request):
    if request.method == "GET":
        return render(request, TEMPLATE, {"values": {}, "errors": {}})
    data, errors = parse_condominium(request.POST)
    if errors:
        return render(request, TEMPLATE, {"values": request.POST, "errors": errors})
    condominium = handle(data)
    messages.success(request, f"Condomínio “{condominium.name}” criado.")
    return redirect("condominiums:list")
