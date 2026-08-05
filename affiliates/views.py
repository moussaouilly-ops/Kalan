import uuid

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course
from .models import AffiliateClick, AffiliateCommission, AffiliateLink, AffiliateProfile
from .serializers import (
    AffiliateCommissionSerializer,
    AffiliateLinkSerializer,
    AffiliateProfileSerializer,
)


class BecomeAffiliateView(APIView):
    """POST /api/v1/affiliates/join/ — n'importe quel utilisateur connecté peut devenir affilié."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile, created = AffiliateProfile.objects.get_or_create(
            user=request.user,
            defaults={"affiliate_code": f"AFF-{uuid.uuid4().hex[:8].upper()}"},
        )
        return Response(AffiliateProfileSerializer(profile).data, status=201 if created else 200)


class MyAffiliateProfileView(generics.RetrieveAPIView):
    serializer_class = AffiliateProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(AffiliateProfile, user=self.request.user)


class AffiliateLinkViewSet(viewsets.ModelViewSet):
    """CRUD des liens d'affiliation de l'utilisateur connecté."""

    serializer_class = AffiliateLinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AffiliateLink.objects.filter(affiliate__user=self.request.user).select_related("course")

    def perform_create(self, serializer):
        profile = get_object_or_404(AffiliateProfile, user=self.request.user)
        course = get_object_or_404(Course, id=self.request.data.get("course"))
        serializer.save(affiliate=profile, course=course)


class TrackClickView(APIView):
    """
    GET /api/v1/affiliates/track/<tracking_code>/ — enregistre un clic sur un
    lien d'affiliation et redirige vers le cours concerné (le frontend gère
    la redirection réelle ; ici on renvoie juste l'ID du cours et confirme
    l'enregistrement du clic, avant que le frontend redirige et applique le
    cookie/paramètre d'attribution pour la conversion à l'achat).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, tracking_code):
        link = get_object_or_404(AffiliateLink, tracking_code=tracking_code)
        AffiliateClick.objects.create(
            link=link,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        link.total_clicks += 1
        link.save(update_fields=["total_clicks"])
        return Response({"course_slug": link.course.slug, "course_id": str(link.course.id)})


class MyCommissionsView(generics.ListAPIView):
    """GET /api/v1/affiliates/my-commissions/ — commissions de l'affilié connecté."""

    serializer_class = AffiliateCommissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AffiliateCommission.objects.filter(affiliate__user=self.request.user)
