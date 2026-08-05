"""Routes de l'app 'core' — recherche globale."""

from django.urls import path

from .views import GlobalSearchView

app_name = "core"

urlpatterns = [
    path("", GlobalSearchView.as_view(), name="global-search"),
]
