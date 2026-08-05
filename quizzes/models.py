import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import Course, Lesson


class Quiz(models.Model):
    """Quiz à choix multiples rattaché à une leçon ou à un cours entier (examen final)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name="quiz", null=True, blank=True)
    title = models.CharField(_("titre"), max_length=255)
    description = models.TextField(blank=True)
    passing_score_percent = models.PositiveSmallIntegerField(_("score minimum pour réussir (%)"), default=70)
    time_limit_minutes = models.PositiveIntegerField(_("durée limite (minutes)"), null=True, blank=True)
    max_attempts = models.PositiveSmallIntegerField(_("tentatives maximum"), default=0, help_text=_("0 = illimité"))
    is_final_exam = models.BooleanField(_("examen final du cours"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("quiz")
        verbose_name_plural = _("quiz")
        ordering = ["course", "created_at"]

    def __str__(self):
        return self.title


class Question(models.Model):
    """Question à choix multiples (une ou plusieurs bonnes réponses)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField(_("énoncé"))
    explanation = models.TextField(_("explication (affichée après correction)"), blank=True)
    order = models.PositiveIntegerField(default=0)
    points = models.PositiveSmallIntegerField(default=1)
    allow_multiple_answers = models.BooleanField(_("plusieurs réponses correctes possibles"), default=False)

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")
        ordering = ["quiz", "order"]

    def __str__(self):
        return self.text[:80]


class Choice(models.Model):
    """Option de réponse pour une question."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(_("texte"), max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("choix de réponse")
        verbose_name_plural = _("choix de réponse")
        ordering = ["question", "order"]

    def __str__(self):
        return self.text[:80]


class QuizAttempt(models.Model):
    """Tentative d'un étudiant sur un quiz, corrigée automatiquement."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    score_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("tentative de quiz")
        verbose_name_plural = _("tentatives de quiz")
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.student} — {self.quiz} ({self.score_percent}%)"


class QuizAnswer(models.Model):
    """Réponse(s) sélectionnée(s) par l'étudiant pour une question donnée, dans une tentative."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected_choices = models.ManyToManyField(Choice, related_name="selected_in_answers")
    is_correct = models.BooleanField(default=False)
    points_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("réponse au quiz")
        verbose_name_plural = _("réponses au quiz")
        unique_together = [("attempt", "question")]


class Certificate(models.Model):
    """Certificat de réussite généré automatiquement à la fin d'un cours."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates")
    certificate_number = models.CharField(max_length=64, unique=True, db_index=True)
    pdf_file = models.FileField(upload_to="certificates/%Y/%m/", blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    final_score_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = _("certificat")
        verbose_name_plural = _("certificats")
        unique_together = [("student", "course")]
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Certificat {self.certificate_number} — {self.student}"
