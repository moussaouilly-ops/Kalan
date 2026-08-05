from rest_framework import serializers

from .models import Review, ReviewHelpfulVote


class ReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.get_full_name", read_only=True)
    student_avatar = serializers.ImageField(source="student.avatar", read_only=True)
    helpful_count = serializers.IntegerField(source="helpful_votes.count", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id", "course", "student", "student_name", "student_avatar", "rating",
            "comment", "instructor_reply", "instructor_replied_at",
            "helpful_count", "created_at", "updated_at",
        ]
        read_only_fields = ["student", "instructor_reply", "instructor_replied_at", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)


class InstructorReplySerializer(serializers.Serializer):
    instructor_reply = serializers.CharField()


class ReviewHelpfulVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewHelpfulVote
        fields = ["id", "review", "created_at"]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
