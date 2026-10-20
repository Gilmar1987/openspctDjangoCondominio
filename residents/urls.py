from django.urls import path

from residents.features import create_resident, delete_resident, get_resident, list_residents, update_resident
from shared.http import api_route

# Montadas sob condominios/<uuid:condominium_id>/moradores/ (ADR-0013).
page_urlpatterns = [
    path("", list_residents.page, name="list"),
    path("novo/", create_resident.page, name="create"),
    path("<uuid:resident_id>/", get_resident.page, name="detail"),
    path("<uuid:resident_id>/editar/", update_resident.page, name="update"),
    path("<uuid:resident_id>/excluir/", delete_resident.page, name="delete"),
]

api_urlpatterns = [
    path("", api_route(get=list_residents.api, post=create_resident.api), name="api-collection"),
    path(
        "<uuid:resident_id>/",
        api_route(get=get_resident.api, put=update_resident.api, delete=delete_resident.api),
        name="api-detail",
    ),
]
