"""Routes de l'app 'courses'."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    ChapterViewSet,
    CourseViewSet,
    LessonProgressUpdateView,
    LessonViewSet,
    MyEnrollmentsView,
    NoteViewSet,
    WishlistViewSet,
)

app_name = "courses"

router = DefaultRouter()
# Désactive les suffixes de format (.json, .api) : évite un conflit
# d'enregistrement de convertisseur d'URL quand plusieurs routeurs DRF
# coexistent dans le même projet (plusieurs apps ici).
router.include_format_suffixes = False
router.register("categories", CategoryViewSet, basename="category")
router.register("courses", CourseViewSet, basename="course")
router.register("chapters", ChapterViewSet, basename="chapter")
router.register("lessons", LessonViewSet, basename="lesson")
router.register("notes", NoteViewSet, basename="note")
router.register("wishlist", WishlistViewSet, basename="wishlist")

urlpatterns = [
    path("", include(router.urls)),
    path("enrollments/", MyEnrollmentsView.as_view(), name="my-enrollments"),
    path("progress/", LessonProgressUpdateView.as_view(), name="progress-update"),
]
