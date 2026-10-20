from django.urls import include, path
from django.views.generic import RedirectView

from apartments import urls as apartment_urls
from condominiums import urls as condominium_urls

TENANT = "condominios/<uuid:condominium_id>/"

urlpatterns = [
    path("", RedirectView.as_view(url="/condominios/", permanent=False)),
    path("condominios/", include((condominium_urls.page_urlpatterns, "condominiums"))),
    path(f"{TENANT}apartamentos/", include((apartment_urls.page_urlpatterns, "apartments"))),
    path("api/condominios/", include((condominium_urls.api_urlpatterns, "condominiums_api"))),
    path(f"api/{TENANT}apartamentos/", include((apartment_urls.api_urlpatterns, "apartments_api"))),
]
