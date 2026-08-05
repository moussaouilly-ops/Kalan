"""Routes de l'app 'affiliates'."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AffiliateLinkViewSet,
    BecomeAffiliateView,
    MyAffiliateProfileView,
    MyCommissionsView,
    TrackClickView,
)

app_name = "affiliates"

router = DefaultRouter()
# Désactive les suffixes de format (.json, .api) : évite un conflit
# d'enregistrement de convertisseur d'URL quand plusieurs routeurs DRF
# coexistent dans le même projet (plusieurs apps ici).
router.include_format_suffixes = False
router.register("links", AffiliateLinkViewSet, basename="affiliate-link")

urlpatterns = [
    path("", include(router.urls)),
    path("join/", BecomeAffiliateView.as_view(), name="join"),
    path("me/", MyAffiliateProfileView.as_view(), name="me"),
    path("track/<str:tracking_code>/", TrackClickView.as_view(), name="track"),
    path("my-commissions/", MyCommissionsView.as_view(), name="my-commissions"),
]
