from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import (
    Category,
    Chapter,
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    Note,
    WishlistItem,
)
from .permissions import IsInstructor, IsInstructorOwnerOrReadOnly
from .serializers import (
    CategorySerializer,
    ChapterWriteSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CourseWriteSerializer,
    EnrollmentSerializer,
    LessonDetailSerializer,
    LessonProgressSerializer,
    LessonWriteSerializer,
    NoteSerializer,
    WishlistItemSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/courses/categories/ — catalogue des catégories, lecture publique."""

    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"


class CourseViewSet(viewsets.ModelViewSet):
    """
    GET  /api/v1/courses/courses/            — catalogue public (cours publiés uniquement)
    GET  /api/v1/courses/courses/{slug}/      — fiche cours complète
    POST /api/v1/courses/courses/             — création (formateur connecté)
    PATCH/DELETE .../{slug}/                  — réservé au formateur propriétaire
    """

    permission_classes = [IsInstructorOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "level", "pricing_model", "instructor"]
    search_fields = ["title", "subtitle", "description"]
    ordering_fields = ["price", "average_rating", "total_students", "created_at"]
    lookup_field = "slug"

    def get_queryset(self):
        user = self.request.user
        base = Course.objects.select_related("instructor", "category")
        if user.is_authenticated and (user.is_staff or user.role == "instructor"):
            # Un formateur voit aussi ses propres brouillons ; le public ne voit que le publié.
            return base.filter(Q(status=Course.Status.PUBLISHED) | Q(instructor=user)).distinct()
        return base.filter(status=Course.Status.PUBLISHED)

    def get_serializer_class(self):
        if self.action in ("list",):
            return CourseListSerializer
        if self.action in ("retrieve",):
            return CourseDetailSerializer
        return CourseWriteSerializer

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user, status=Course.Status.DRAFT)


class ChapterViewSet(viewsets.ModelViewSet):
    """CRUD des chapitres — réservé au formateur propriétaire du cours parent."""

    serializer_class = ChapterWriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOwnerOrReadOnly]

    def get_queryset(self):
        return Chapter.objects.filter(course_id=self.kwargs.get("course_pk")) \
            if self.kwargs.get("course_pk") else Chapter.objects.all()


class LessonViewSet(viewsets.ModelViewSet):
    """
    CRUD des leçons. Le contenu vidéo complet n'est renvoyé que si la leçon
    est un aperçu gratuit, ou si l'étudiant est inscrit au cours.
    """

    serializer_class = LessonWriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOwnerOrReadOnly]

    def get_queryset(self):
        return Lesson.objects.select_related("chapter__course")

    def retrieve(self, request, *args, **kwargs):
        lesson = self.get_object()
        user = request.user
        has_access = lesson.is_preview or (
            user.is_authenticated and (
                user.is_staff
                or lesson.chapter.course.instructor_id == user.id
                or Enrollment.objects.filter(
                    student=user, course=lesson.chapter.course, is_active=True
                ).exists()
            )
        )
        if not has_access:
            return Response(
                {"detail": "Inscription requise pour accéder au contenu complet de cette leçon."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(LessonDetailSerializer(lesson).data)


class MyEnrollmentsView(generics.ListAPIView):
    """GET /api/v1/courses/enrollments/ — cours suivis par l'étudiant connecté."""

    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user).select_related("course")


class LessonProgressUpdateView(APIView):
    """
    POST /api/v1/courses/progress/ — enregistre la position de lecture
    (reprise automatique) et marque la leçon comme terminée si besoin.
    Body : {"lesson": "<uuid>", "last_position_seconds": 125, "is_completed": false}
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        lesson_id = request.data.get("lesson")
        lesson = get_object_or_404(Lesson, id=lesson_id)
        enrollment = get_object_or_404(
            Enrollment, student=request.user, course=lesson.chapter.course, is_active=True
        )
        progress, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
        progress.last_position_seconds = request.data.get("last_position_seconds", progress.last_position_seconds)
        if request.data.get("is_completed") and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
        progress.save()

        # Recalcule le pourcentage de progression global du cours.
        total_lessons = Lesson.objects.filter(chapter__course=enrollment.course).count()
        completed_lessons = LessonProgress.objects.filter(enrollment=enrollment, is_completed=True).count()
        if total_lessons:
            enrollment.progress_percent = round((completed_lessons / total_lessons) * 100)
            if enrollment.progress_percent >= 100 and not enrollment.completed_at:
                enrollment.completed_at = timezone.now()
            enrollment.save(update_fields=["progress_percent", "completed_at"])

        return Response(LessonProgressSerializer(progress).data)


class NoteViewSet(viewsets.ModelViewSet):
    """Notes personnelles prises pendant une vidéo — visibles uniquement par leur auteur."""

    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Note.objects.filter(student=self.request.user)
        lesson_id = self.request.query_params.get("lesson")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        return qs


class WishlistViewSet(viewsets.ModelViewSet):
    """Liste de souhaits de l'étudiant connecté."""

    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(student=self.request.user).select_related("course")
