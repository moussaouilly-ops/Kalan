import uuid

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Enrollment
from .models import Certificate, Choice, Question, Quiz, QuizAnswer, QuizAttempt
from .serializers import (
    CertificateSerializer,
    QuizAttemptSerializer,
    QuizSerializer,
    SubmitQuizAttemptSerializer,
)


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/quizzes/quizzes/ — lecture seule ; la création se fait via l'admin/formateur (à étendre)."""

    queryset = Quiz.objects.prefetch_related("questions__choices")
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]


class SubmitQuizAttemptView(APIView):
    """
    POST /api/v1/quizzes/<quiz_id>/submit/ — soumet les réponses et corrige
    automatiquement. Body: {"answers": [{"question": "<uuid>", "selected_choices": ["<uuid>", ...]}]}
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        serializer = SubmitQuizAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if quiz.max_attempts:
            previous_attempts = QuizAttempt.objects.filter(quiz=quiz, student=request.user).count()
            if previous_attempts >= quiz.max_attempts:
                return Response({"detail": "Nombre maximum de tentatives atteint pour ce quiz."}, status=400)

        attempt = QuizAttempt.objects.create(quiz=quiz, student=request.user)

        total_points = 0
        earned_points = 0

        for answer_data in serializer.validated_data["answers"]:
            question = get_object_or_404(Question, id=answer_data["question"], quiz=quiz)
            selected_ids = set(str(c) for c in answer_data["selected_choices"])
            correct_ids = set(str(c) for c in question.choices.filter(is_correct=True).values_list("id", flat=True))

            is_correct = selected_ids == correct_ids
            points_awarded = question.points if is_correct else 0

            quiz_answer = QuizAnswer.objects.create(
                attempt=attempt, question=question, is_correct=is_correct, points_awarded=points_awarded,
            )
            quiz_answer.selected_choices.set(Choice.objects.filter(id__in=selected_ids))

            total_points += question.points
            earned_points += points_awarded

        score_percent = round((earned_points / total_points) * 100, 2) if total_points else 0
        attempt.score_percent = score_percent
        attempt.is_passed = score_percent >= quiz.passing_score_percent
        attempt.submitted_at = timezone.now()
        attempt.save()

        # Si c'est l'examen final du cours et qu'il est réussi, on émet le certificat.
        if quiz.is_final_exam and attempt.is_passed:
            _issue_certificate_if_needed(request.user, quiz.course, score_percent)

        return Response(QuizAttemptSerializer(attempt).data, status=201)


def _issue_certificate_if_needed(student, course, score_percent):
    if Certificate.objects.filter(student=student, course=course).exists():
        return
    Certificate.objects.create(
        student=student,
        course=course,
        certificate_number=f"KLN-CERT-{uuid.uuid4().hex[:10].upper()}",
        final_score_percent=score_percent,
    )
    Enrollment.objects.filter(student=student, course=course).update(certificate_issued=True)


class MyQuizAttemptsView(generics.ListAPIView):
    """GET /api/v1/quizzes/my-attempts/?quiz=<uuid> — historique des tentatives de l'étudiant."""

    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = QuizAttempt.objects.filter(student=self.request.user).prefetch_related("answers")
        quiz_id = self.request.query_params.get("quiz")
        if quiz_id:
            qs = qs.filter(quiz_id=quiz_id)
        return qs


class MyCertificatesView(generics.ListAPIView):
    """GET /api/v1/quizzes/my-certificates/ — certificats obtenus par l'étudiant connecté."""

    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Certificate.objects.filter(student=self.request.user)
