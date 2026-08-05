from django.contrib import admin

from .models import Category, Chapter, Course, Enrollment, Lesson, LessonProgress, LessonResource, Note, WishlistItem


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_active", "order"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "instructor", "category", "status", "price", "total_students", "average_rating", "created_at"]
    list_filter = ["status", "level", "pricing_model", "category"]
    search_fields = ["title", "instructor__email"]
    inlines = [ChapterInline]
    readonly_fields = ["total_students", "average_rating", "total_reviews", "total_duration_seconds"]


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "order"]
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "chapter", "content_type", "is_preview", "video_duration_seconds"]
    list_filter = ["content_type", "is_preview"]


admin.site.register(LessonResource)
admin.site.register(Enrollment)
admin.site.register(LessonProgress)
admin.site.register(Note)
admin.site.register(WishlistItem)
