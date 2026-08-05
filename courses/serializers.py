from rest_framework import serializers

from .models import (
    Category,
    Chapter,
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    LessonResource,
    Note,
    WishlistItem,
)


class CategorySerializer(serializers.ModelSerializer):
    course_count = serializers.IntegerField(source="courses.count", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "icon", "parent", "order", "course_count"]


class LessonResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonResource
        fields = ["id", "title", "file", "file_size_bytes", "is_downloadable"]


class LessonSerializer(serializers.ModelSerializer):
    """
    Leçon telle que renvoyée dans le programme d'un cours.
    Le contenu vidéo complet (video_url/video_file) n'est exposé que si
    l'étudiant y a droit — voir LessonDetailSerializer pour la version complète.
    """

    resources = LessonResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id", "title", "content_type", "order", "video_duration_seconds",
            "is_preview", "is_downloadable", "resources",
        ]


class LessonDetailSerializer(LessonSerializer):
    """Version complète d'une leçon, avec le contenu vidéo/texte — réservée aux inscrits."""

    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + ["video_file", "video_url", "text_content"]


class ChapterSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = ["id", "title", "description", "order", "lessons"]


class CourseListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes/le catalogue."""

    instructor_name = serializers.CharField(source="instructor.get_full_name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "subtitle", "category", "category_name",
            "instructor", "instructor_name", "level", "language", "thumbnail",
            "pricing_model", "price", "discount_price", "effective_price",
            "average_rating", "total_reviews", "total_students",
            "total_duration_seconds", "is_featured", "status",
        ]
        read_only_fields = ["average_rating", "total_reviews", "total_students", "status"]


class CourseDetailSerializer(CourseListSerializer):
    """Version complète pour la fiche cours, avec le programme (chapitres/leçons)."""

    chapters = ChapterSerializer(many=True, read_only=True)

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + [
            "description", "what_you_will_learn", "requirements", "target_audience",
            "promo_video", "chapters", "created_at", "published_at",
        ]


class CourseWriteSerializer(serializers.ModelSerializer):
    """Utilisé par les formateurs pour créer/modifier leurs propres cours."""

    class Meta:
        model = Course
        fields = [
            "id", "category", "title", "subtitle", "description",
            "what_you_will_learn", "requirements", "target_audience",
            "language", "level", "thumbnail", "promo_video",
            "pricing_model", "price", "discount_price", "status",
        ]
        read_only_fields = ["id"]

    def validate_status(self, value):
        # Un formateur ne peut pas se publier lui-même : il passe par "pending_review".
        if value == Course.Status.PUBLISHED:
            raise serializers.ValidationError(
                "Seul un administrateur peut publier un cours. Choisissez 'pending_review'."
            )
        return value

    def create(self, validated_data):
        validated_data["instructor"] = self.context["request"].user
        return super().create(validated_data)


class ChapterWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ["id", "course", "title", "description", "order"]


class LessonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id", "chapter", "title", "content_type", "order",
            "video_file", "video_url", "video_duration_seconds",
            "text_content", "is_preview", "is_downloadable",
        ]


class EnrollmentSerializer(serializers.ModelSerializer):
    course_detail = CourseListSerializer(source="course", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id", "course", "course_detail", "source", "enrolled_at",
            "completed_at", "progress_percent", "is_active", "certificate_issued",
        ]
        read_only_fields = ["progress_percent", "completed_at", "certificate_issued", "enrolled_at"]


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = [
            "id", "enrollment", "lesson", "is_completed",
            "last_position_seconds", "watched_seconds_total", "completed_at",
        ]
        read_only_fields = ["completed_at"]


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "lesson", "timestamp_seconds", "content", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)


class WishlistItemSerializer(serializers.ModelSerializer):
    course_detail = CourseListSerializer(source="course", read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "course", "course_detail", "added_at"]

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)
