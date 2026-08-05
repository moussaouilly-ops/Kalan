import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import Course


class Review(models.Model):
    """Avis noté (1 à 5) laissé par un étudiant inscrit sur un cours."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    instructor_reply = models.TextField(_("réponse du formateur"), blank=True)
    instructor_replied_at = models.DateTimeField(null=True, blank=True)
    is_flagged = models.BooleanField(_("signalé pour modération"), default=False)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("avis")
        verbose_name_plural = _("avis")
        unique_together = [("course", "student")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} — {self.course} ({self.rating}/5)"


class ReviewHelpfulVote(models.Model):
    """Vote 'utile' sur un avis, façon Udemy."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="helpful_votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("vote utile")
        verbose_name_plural = _("votes utiles")
        unique_together = [("review", "user")]
