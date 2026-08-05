from rest_framework import permissions


class IsInstructorOwnerOrReadOnly(permissions.BasePermission):
    """
    Lecture libre pour tout le monde. Écriture réservée au formateur
    propriétaire du cours (ou à un administrateur).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        course = obj if hasattr(obj, "instructor") else getattr(obj, "course", None)
        if course is None and hasattr(obj, "chapter"):
            course = obj.chapter.course
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or course.instructor_id == user.id))


class IsInstructor(permissions.BasePermission):
    """Autorise uniquement les utilisateurs ayant le rôle formateur (ou admin)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.role == "instructor"))
