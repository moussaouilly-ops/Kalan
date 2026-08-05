from rest_framework import serializers

from .models import Certificate, Choice, Question, Quiz, QuizAnswer, QuizAttempt


class ChoiceSerializer(serializers.ModelSerializer):
    """
    Ne renvoie jamais `is_correct` à l'étudiant avant qu'il ait soumis sa
    tentative — voir ChoiceStudentSerializer plus bas.
    """

    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct", "order"]


class ChoiceStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "order"]  # is_correct volontairement absent


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "points", "allow_multiple_answers", "choices"]


class QuestionWithAnswersSerializer(QuestionSerializer):
    """Version formateur, avec les bonnes réponses et l'explication — pour la gestion du quiz."""

    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta(QuestionSerializer.Meta):
        fields = QuestionSerializer.Meta.fields + ["explanation"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.IntegerField(source="questions.count", read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id", "course", "lesson", "title", "description",
            "passing_score_percent", "time_limit_minutes", "max_attempts",
            "is_final_exam", "questions", "question_count",
        ]


class SubmitAnswerSerializer(serializers.Serializer):
    question = serializers.UUIDField()
    selected_choices = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)


class SubmitQuizAttemptSerializer(serializers.Serializer):
    """Corps de requête pour soumettre une tentative complète, corrigée automatiquement."""

    answers = SubmitAnswerSerializer(many=True)


class QuizAnswerResultSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text", read_only=True)
    explanation = serializers.CharField(source="question.explanation", read_only=True)
    correct_choice_ids = serializers.SerializerMethodField()

    class Meta:
        model = QuizAnswer
        fields = [
            "question", "question_text", "explanation", "selected_choices",
            "correct_choice_ids", "is_correct", "points_awarded",
        ]

    def get_correct_choice_ids(self, obj):
        return list(obj.question.choices.filter(is_correct=True).values_list("id", flat=True))


class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = QuizAnswerResultSerializer(many=True, read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id", "quiz", "quiz_title", "score_percent", "is_passed",
            "started_at", "submitted_at", "answers",
        ]
        read_only_fields = ["score_percent", "is_passed", "started_at", "submitted_at"]


class CertificateSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    student_name = serializers.CharField(source="student.get_full_name", read_only=True)

    class Meta:
        model = Certificate
        fields = [
            "id", "course", "course_title", "student_name", "certificate_number",
            "pdf_file", "issued_at", "final_score_percent",
        ]
        read_only_fields = fields
