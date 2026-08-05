from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import InstructorProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Représentation publique d'un utilisateur (profil, réponses API)."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "phone_number", "role", "avatar", "bio", "country", "city",
            "headline", "is_verified_instructor", "email_verified", "date_joined",
        ]
        read_only_fields = ["id", "role", "is_verified_instructor", "email_verified", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    """Inscription : e-mail + mot de passe + rôle choisi (étudiant ou formateur)."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm", "first_name", "last_name", "role"]

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("Ce rôle ne peut pas être choisi à l'inscription.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if user.role == User.Role.INSTRUCTOR:
            InstructorProfile.objects.create(user=user)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Changement de mot de passe pour un utilisateur déjà connecté."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class PasswordResetRequestSerializer(serializers.Serializer):
    """Étape 1 : l'utilisateur demande un lien de réinitialisation par e-mail."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Étape 2 : l'utilisateur soumet le jeton reçu par e-mail + son nouveau mot de passe."""

    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class InstructorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = InstructorProfile
        fields = [
            "user", "website", "facebook_url", "linkedin_url",
            "total_students", "total_courses", "average_rating",
            "payout_provider", "payout_phone_number",
        ]
