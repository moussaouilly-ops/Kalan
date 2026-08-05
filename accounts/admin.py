from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import EmailVerificationToken, InstructorProfile, PasswordResetToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "first_name", "last_name", "role", "is_active", "email_verified", "date_joined"]
    list_filter = ["role", "is_active", "email_verified", "is_verified_instructor"]
    search_fields = ["email", "first_name", "last_name", "phone_number"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name", "phone_number", "avatar", "bio", "country", "city")}),
        ("Rôle", {"fields": ("role", "headline", "is_verified_instructor")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "email_verified", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role")}),
    )


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "total_students", "total_courses", "average_rating"]
    search_fields = ["user__email"]


admin.site.register(EmailVerificationToken)
admin.site.register(PasswordResetToken)
