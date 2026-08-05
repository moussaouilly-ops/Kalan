import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager pour le modèle User personnalisé (connexion par e-mail)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.STUDENT)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Utilisateur de la plateforme. La connexion se fait par e-mail."""

    class Role(models.TextChoices):
        STUDENT = "student", _("Étudiant")
        INSTRUCTOR = "instructor", _("Formateur")
        ADMIN = "admin", _("Administrateur")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("adresse e-mail"), unique=True, db_index=True)
    first_name = models.CharField(_("prénom"), max_length=150, blank=True)
    last_name = models.CharField(_("nom"), max_length=150, blank=True)
    phone_number = models.CharField(_("numéro de téléphone"), max_length=20, blank=True)
    role = models.CharField(_("rôle"), max_length=20, choices=Role.choices, default=Role.STUDENT)

    avatar = models.ImageField(_("avatar"), upload_to="avatars/%Y/%m/", blank=True, null=True)
    bio = models.TextField(_("biographie"), blank=True)
    country = models.CharField(_("pays"), max_length=100, blank=True, default="Burkina Faso")
    city = models.CharField(_("ville"), max_length=100, blank=True)

    headline = models.CharField(_("titre professionnel"), max_length=255, blank=True)
    is_verified_instructor = models.BooleanField(_("formateur vérifié"), default=False)

    is_active = models.BooleanField(_("actif"), default=True)
    is_staff = models.BooleanField(_("accès admin Django"), default=False)
    email_verified = models.BooleanField(_("e-mail vérifié"), default=False)

    date_joined = models.DateTimeField(_("date d'inscription"), default=timezone.now)
    last_login = models.DateTimeField(_("dernière connexion"), blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("utilisateur")
        verbose_name_plural = _("utilisateurs")
        ordering = ["-date_joined"]

    def __str__(self):
        return self.get_full_name() or self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name or self.email

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN


class EmailVerificationToken(models.Model):
    """Jeton envoyé par e-mail pour valider l'adresse à l'inscription."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="verification_tokens")
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("jeton de vérification e-mail")
        verbose_name_plural = _("jetons de vérification e-mail")

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at


class PasswordResetToken(models.Model):
    """Jeton pour la réinitialisation de mot de passe."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("jeton de réinitialisation")
        verbose_name_plural = _("jetons de réinitialisation")

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at


class InstructorProfile(models.Model):
    """Informations complémentaires publiques d'un formateur."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="instructor_profile",
        limit_choices_to={"role": User.Role.INSTRUCTOR},
    )
    website = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    total_students = models.PositiveIntegerField(default=0)
    total_courses = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    payout_provider = models.CharField(
        max_length=20,
        choices=[
            ("orange_money", "Orange Money"),
            ("moov_money", "Moov Money"),
            ("wave", "Wave"),
            ("coris_money", "Coris Money"),
            ("bank", "Compte bancaire"),
        ],
        blank=True,
    )
    payout_phone_number = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = _("profil formateur")
        verbose_name_plural = _("profils formateurs")

    def __str__(self):
        return f"Profil formateur de {self.user}"
