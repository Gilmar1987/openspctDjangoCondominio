from django.urls import include, path
from django.views.generic import RedirectView

from apartments import urls as apartment_urls
from condominiums import urls as condominium_urls
from owners import urls as owner_urls
from residents import urls as resident_urls

TENANT = "condominios/<uuid:condominium_id>/"

urlpatterns = [
    path("", RedirectView.as_view(url="/condominios/", permanent=False)),
    path("condominios/", include((condominium_urls.page_urlpatterns, "condominiums"))),
    path(f"{TENANT}apartamentos/", include((apartment_urls.page_urlpatterns, "apartments"))),
    path(f"{TENANT}proprietarios/", include((owner_urls.page_urlpatterns, "owners"))),
    path(f"{TENANT}moradores/", include((resident_urls.page_urlpatterns, "residents"))),
    path("api/condominios/", include((condominium_urls.api_urlpatterns, "condominiums_api"))),
    path(f"api/{TENANT}apartamentos/", include((apartment_urls.api_urlpatterns, "apartments_api"))),
    path(f"api/{TENANT}proprietarios/", include((owner_urls.api_urlpatterns, "owners_api"))),
    path(f"api/{TENANT}moradores/", include((resident_urls.api_urlpatterns, "residents_api"))),
]
