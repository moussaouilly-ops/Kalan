from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Conversation, Message

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "sender_name", "body", "attachment", "is_read", "created_at"]
        read_only_fields = ["sender", "is_read", "created_at"]

    def create(self, validated_data):
        validated_data["sender"] = self.context["request"].user
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    other_participant_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "participants", "course", "created_at", "last_message_at",
            "other_participant_name", "last_message", "unread_count",
        ]
        read_only_fields = ["created_at", "last_message_at"]

    def get_other_participant_name(self, obj):
        request_user = self.context["request"].user
        other = obj.participants.exclude(id=request_user.id).first()
        return other.get_full_name() if other else None

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        return last.body[:120] if last else None

    def get_unread_count(self, obj):
        request_user = self.context["request"].user
        return obj.messages.filter(is_read=False).exclude(sender=request_user).count()


class StartConversationSerializer(serializers.Serializer):
    """Démarre (ou récupère) une conversation avec un autre utilisateur, avec un premier message."""

    recipient = serializers.UUIDField()
    course = serializers.UUIDField(required=False)
    body = serializers.CharField()
