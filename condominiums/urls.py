from django.urls import path

from condominiums.features import create_condominium, get_condominium, list_condominiums
from shared.http import api_route

page_urlpatterns = [
    path("", list_condominiums.page, name="list"),
    path("novo/", create_condominium.page, name="create"),
    path("<uuid:condominium_id>/", get_condominium.page, name="detail"),
]

api_urlpatterns = [
    path("", api_route(get=list_condominiums.api, post=create_condominium.api), name="api-collection"),
    path("<uuid:condominium_id>/", api_route(get=get_condominium.api), name="api-detail"),
]
