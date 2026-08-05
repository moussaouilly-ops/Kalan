import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PasswordResetToken
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — inscription (étudiant ou formateur)."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = _tokens_for_user(user)
        return Response(
            {"user": UserSerializer(user).data, **tokens},
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/auth/me/ — profil de l'utilisateur connecté."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/v1/auth/change-password/ — pour un utilisateur déjà connecté."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"old_password": "Mot de passe actuel incorrect."}, status=400)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Mot de passe mis à jour."})


class PasswordResetRequestView(APIView):
    """POST /api/v1/auth/password-reset/ — envoie un e-mail avec un jeton de réinitialisation."""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # On répond toujours la même chose, pour ne pas révéler quels e-mails existent.
            return Response({"detail": "Si ce compte existe, un e-mail a été envoyé."})

        token_value = uuid.uuid4().hex
        PasswordResetToken.objects.create(
            user=user,
            token=token_value,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        reset_link = f"{settings.FRONTEND_URL}/reinitialiser-mot-de-passe?token={token_value}"
        send_mail(
            subject="Réinitialisation de votre mot de passe",
            message=f"Voici votre lien de réinitialisation (valable 1 heure) : {reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return Response({"detail": "Si ce compte existe, un e-mail a été envoyé."})


class PasswordResetConfirmView(APIView):
    """POST /api/v1/auth/password-reset/confirm/ — applique le nouveau mot de passe."""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reset_token = PasswordResetToken.objects.get(token=serializer.validated_data["token"])
        except PasswordResetToken.DoesNotExist:
            return Response({"token": "Jeton invalide."}, status=400)

        if not reset_token.is_valid():
            return Response({"token": "Jeton expiré ou déjà utilisé."}, status=400)

        user = reset_token.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        reset_token.used = True
        reset_token.save(update_fields=["used"])
        return Response({"detail": "Mot de passe réinitialisé avec succès."})


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — met le refresh token en liste noire."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data["refresh"])
            token.blacklist()
        except Exception:
            return Response({"detail": "Jeton invalide."}, status=400)
        return Response({"detail": "Déconnexion réussie."})
