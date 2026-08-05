from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import UserSerializer
from courses.models import Category, Course
from courses.serializers import CategorySerializer, CourseListSerializer

User = get_user_model()


class GlobalSearchView(APIView):
    """
    GET /api/v1/search/?q=... — recherche transverse sur les cours, les
    formateurs et les catégories. En production, remplacer le filtrage
    `icontains` ci-dessous par la recherche plein texte de PostgreSQL
    (SearchVector/SearchRank, déjà activée via 'django.contrib.postgres'
    dans INSTALLED_APPS) pour de meilleurs résultats de pertinence.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"courses": [], "instructors": [], "categories": []})

        courses = Course.objects.filter(
            Q(status=Course.Status.PUBLISHED)
            & (Q(title__icontains=query) | Q(subtitle__icontains=query) | Q(description__icontains=query))
        )[:20]

        instructors = User.objects.filter(
            role=User.Role.INSTRUCTOR
        ).filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(headline__icontains=query)
        )[:10]

        categories = Category.objects.filter(is_active=True, name__icontains=query)[:10]

        return Response({
            "courses": CourseListSerializer(courses, many=True).data,
            "instructors": UserSerializer(instructors, many=True).data,
            "categories": CategorySerializer(categories, many=True).data,
        })
