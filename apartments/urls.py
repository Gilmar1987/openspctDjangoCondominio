from django.urls import path

from apartments.features import (
    create_apartment,
    delete_apartment,
    get_apartment,
    list_apartments,
    update_apartment,
)
from shared.http import api_route

# Montadas sob condominios/<uuid:condominium_id>/apartamentos/ (ADR-0013).
page_urlpatterns = [
    path("", list_apartments.page, name="list"),
    path("novo/", create_apartment.page, name="create"),
    path("<uuid:apartment_id>/editar/", update_apartment.page, name="update"),
    path("<uuid:apartment_id>/excluir/", delete_apartment.page, name="delete"),
]

api_urlpatterns = [
    path("", api_route(get=list_apartments.api, post=create_apartment.api), name="api-collection"),
    path(
        "<uuid:apartment_id>/",
        api_route(get=get_apartment.api, put=update_apartment.api, delete=delete_apartment.api),
        name="api-detail",
    ),
]
