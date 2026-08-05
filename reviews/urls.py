"""Routes de l'app 'reviews'."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReviewViewSet

app_name = "reviews"

router = DefaultRouter()
# Désactive les suffixes de format (.json, .api) : évite un conflit
# d'enregistrement de convertisseur d'URL quand plusieurs routeurs DRF
# coexistent dans le même projet (plusieurs apps ici).
router.include_format_suffixes = False
router.register("reviews", ReviewViewSet, basename="review")

urlpatterns = [
    path("", include(router.urls)),
]
