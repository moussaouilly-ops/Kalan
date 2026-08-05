import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import Course


class Conversation(models.Model):
    """Fil de discussion entre deux utilisateurs (étudiant ↔ formateur), lié à un cours."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversations")
    course = models.ForeignKey(
        Course, on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations",
        help_text=_("Cours concerné, si la discussion en découle"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("conversation")
        verbose_name_plural = _("conversations")
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self):
        return f"Conversation #{str(self.id)[:8]}"


class Message(models.Model):
    """Message individuel dans une conversation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    body = models.TextField()
    attachment = models.FileField(upload_to="messages/attachments/%Y/%m/", blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} — {self.body[:50]}"
