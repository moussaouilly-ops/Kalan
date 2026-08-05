from django.contrib import admin

from .models import Certificate, Choice, Question, Quiz, QuizAnswer, QuizAttempt


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "is_final_exam", "passing_score_percent"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "quiz", "points"]
    inlines = [ChoiceInline]


admin.site.register(QuizAttempt)
admin.site.register(QuizAnswer)
admin.site.register(Certificate)
