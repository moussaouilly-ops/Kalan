from django.contrib import admin

from .models import Review, ReviewHelpfulVote


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["course", "student", "rating", "is_visible", "is_flagged", "created_at"]
    list_filter = ["rating", "is_visible", "is_flagged"]
    search_fields = ["course__title", "student__email"]


admin.site.register(ReviewHelpfulVote)
