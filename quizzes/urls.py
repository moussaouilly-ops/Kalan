"""Routes de l'app 'quizzes'."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MyCertificatesView, MyQuizAttemptsView, QuizViewSet, SubmitQuizAttemptView

app_name = "quizzes"

router = DefaultRouter()
# Désactive les suffixes de format (.json, .api) : évite un conflit
# d'enregistrement de convertisseur d'URL quand plusieurs routeurs DRF
# coexistent dans le même projet (plusieurs apps ici).
router.include_format_suffixes = False
router.register("quizzes", QuizViewSet, basename="quiz")

urlpatterns = [
    path("", include(router.urls)),
    path("<uuid:quiz_id>/submit/", SubmitQuizAttemptView.as_view(), name="submit-attempt"),
    path("my-attempts/", MyQuizAttemptsView.as_view(), name="my-attempts"),
    path("my-certificates/", MyCertificatesView.as_view(), name="my-certificates"),
]
