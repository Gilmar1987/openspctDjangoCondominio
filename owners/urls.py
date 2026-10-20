from django.urls import path

from owners.features import create_owner, delete_owner, get_owner, list_owners, update_owner
from shared.http import api_route

# Montadas sob condominios/<uuid:condominium_id>/proprietarios/ (ADR-0013).
page_urlpatterns = [
    path("", list_owners.page, name="list"),
    path("novo/", create_owner.page, name="create"),
    path("<uuid:owner_id>/", get_owner.page, name="detail"),
    path("<uuid:owner_id>/editar/", update_owner.page, name="update"),
    path("<uuid:owner_id>/excluir/", delete_owner.page, name="delete"),
]

api_urlpatterns = [
    path("", api_route(get=list_owners.api, post=create_owner.api), name="api-collection"),
    path(
        "<uuid:owner_id>/",
        api_route(get=get_owner.api, put=update_owner.api, delete=delete_owner.api),
        name="api-detail",
    ),
]
