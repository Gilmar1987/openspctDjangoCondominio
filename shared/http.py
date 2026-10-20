"""Respostas de erro JSON padronizadas da API (ADR-0014)."""

from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler

NOT_FOUND_DETAIL = "Não encontrado."


def validation_error_response(errors: dict[str, list[str]]) -> Response:
    return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)


def not_found_response() -> Response:
    return Response({"detail": NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)


def api_exception_handler(exc, context):
    if isinstance(exc, Http404):
        return not_found_response()
    return exception_handler(exc, context)


def api_route(**handlers):
    """Monta uma APIView a partir de funções de fatias distintas que compartilham a URL.

    Ex.: api_route(get=list_apartments.api, post=create_apartment.api)
    """

    def bind(fn):
        return lambda self, request, *args, **kwargs: fn(request, *args, **kwargs)

    view = type("SliceRouteView", (APIView,), {m: bind(fn) for m, fn in handlers.items()})
    return view.as_view()


def request_mapping(data) -> dict:
    """Converte o corpo da requisição (dict JSON ou QueryDict) em dict simples."""
    if hasattr(data, "items"):
        return dict(data.items())
    return {}
