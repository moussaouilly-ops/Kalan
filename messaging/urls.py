"""Routes de l'app 'messaging'."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ConversationMessagesView, ConversationViewSet, StartConversationView

app_name = "messaging"

router = DefaultRouter()
# Désactive les suffixes de format (.json, .api) : évite un conflit
# d'enregistrement de convertisseur d'URL quand plusieurs routeurs DRF
# coexistent dans le même projet (plusieurs apps ici).
router.include_format_suffixes = False
router.register("conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("", include(router.urls)),
    path("conversations/<uuid:conversation_id>/messages/", ConversationMessagesView.as_view(), name="messages"),
    path("start/", StartConversationView.as_view(), name="start"),
]
