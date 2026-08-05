from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from courses.models import Enrollment
from .models import Review, ReviewHelpfulVote
from .serializers import InstructorReplySerializer, ReviewHelpfulVoteSerializer, ReviewSerializer


class IsReviewAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.student_id == request.user.id


class ReviewViewSet(viewsets.ModelViewSet):
    """
    GET  /api/v1/reviews/reviews/?course=<uuid>   — avis visibles d'un cours (public)
    POST /api/v1/reviews/reviews/                 — laisser un avis (doit être inscrit au cours)
    POST /api/v1/reviews/reviews/{id}/reply/       — réponse du formateur propriétaire
    POST /api/v1/reviews/reviews/{id}/helpful/     — voter utile
    """

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewAuthorOrReadOnly]

    def get_queryset(self):
        qs = Review.objects.filter(is_visible=True).select_related("student")
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    def perform_create(self, serializer):
        course = serializer.validated_data["course"]
        if not Enrollment.objects.filter(student=self.request.user, course=course, is_active=True).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous devez être inscrit à ce cours pour laisser un avis.")
        review = serializer.save()
        self._refresh_course_rating(course)

    def perform_destroy(self, instance):
        course = instance.course
        instance.delete()
        self._refresh_course_rating(course)

    @staticmethod
    def _refresh_course_rating(course):
        from django.db.models import Avg, Count
        stats = course.reviews.filter(is_visible=True).aggregate(avg=Avg("rating"), total=Count("id"))
        course.average_rating = round(stats["avg"] or 0, 2)
        course.total_reviews = stats["total"] or 0
        course.save(update_fields=["average_rating", "total_reviews"])

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        review = self.get_object()
        if review.course.instructor_id != request.user.id:
            return Response({"detail": "Seul le formateur du cours peut répondre."}, status=403)
        serializer = InstructorReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review.instructor_reply = serializer.validated_data["instructor_reply"]
        review.instructor_replied_at = timezone.now()
        review.save(update_fields=["instructor_reply", "instructor_replied_at"])
        return Response(ReviewSerializer(review).data)

    @action(detail=True, methods=["post"])
    def helpful(self, request, pk=None):
        review = self.get_object()
        vote, created = ReviewHelpfulVote.objects.get_or_create(review=review, user=request.user)
        if not created:
            vote.delete()
            return Response({"detail": "Vote retiré."})
        return Response(ReviewHelpfulVoteSerializer(vote).data, status=201)
