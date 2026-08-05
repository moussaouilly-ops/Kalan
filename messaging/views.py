from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, StartConversationSerializer

User = get_user_model()


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/messaging/conversations/ — conversations de l'utilisateur connecté."""

    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related("messages")


class ConversationMessagesView(APIView):
    """
    GET  /api/v1/messaging/conversations/<id>/messages/ — historique, marque comme lu
    POST /api/v1/messaging/conversations/<id>/messages/ — envoyer un message
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        messages = conversation.messages.select_related("sender")
        messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True, read_at=timezone.now())
        return Response(MessageSerializer(messages, many=True).data)

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        serializer = MessageSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        message = serializer.save(conversation=conversation)
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at"])
        return Response(MessageSerializer(message).data, status=201)


class StartConversationView(APIView):
    """
    POST /api/v1/messaging/start/ — crée (ou réutilise) une conversation avec
    un destinataire, et y poste le premier message.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = StartConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        recipient = get_object_or_404(User, id=data["recipient"])

        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(participants=recipient).first()

        if not conversation:
            conversation = Conversation.objects.create(course_id=data.get("course"))
            conversation.participants.set([request.user, recipient])

        message = Message.objects.create(conversation=conversation, sender=request.user, body=data["body"])
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at"])

        return Response(ConversationSerializer(conversation, context={"request": request}).data, status=201)
