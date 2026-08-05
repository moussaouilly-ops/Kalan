import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import Course
from payments.models import Payment


class AffiliateProfile(models.Model):
    """Profil d'affilié : n'importe quel utilisateur peut promouvoir des cours contre commission."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="affiliate_profile")
    affiliate_code = models.CharField(max_length=20, unique=True, db_index=True)
    commission_percent = models.DecimalField(_("taux de commission (%)"), max_digits=5, decimal_places=2, default=10)
    total_earned = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("profil affilié")
        verbose_name_plural = _("profils affiliés")

    def __str__(self):
        return f"Affilié {self.user} ({self.affiliate_code})"


class AffiliateLink(models.Model):
    """Lien de tracking généré par un affilié pour un cours donné."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    affiliate = models.ForeignKey(AffiliateProfile, on_delete=models.CASCADE, related_name="links")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="affiliate_links")
    tracking_code = models.CharField(max_length=32, unique=True, db_index=True)
    total_clicks = models.PositiveIntegerField(default=0)
    total_conversions = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("lien d'affiliation")
        verbose_name_plural = _("liens d'affiliation")
        unique_together = [("affiliate", "course")]

    def __str__(self):
        return f"{self.affiliate} → {self.course} ({self.tracking_code})"


class AffiliateClick(models.Model):
    """Clic enregistré sur un lien d'affiliation (avant conversion éventuelle)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    link = models.ForeignKey(AffiliateLink, on_delete=models.CASCADE, related_name="clicks")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("clic d'affiliation")
        verbose_name_plural = _("clics d'affiliation")
        ordering = ["-clicked_at"]


class AffiliateCommission(models.Model):
    """Commission due à un affilié suite à une vente confirmée."""

    class Status(models.TextChoices):
        PENDING = "pending", _("En attente")
        APPROVED = "approved", _("Approuvée")
        PAID = "paid", _("Payée")
        CANCELLED = "cancelled", _("Annulée (remboursement)")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    affiliate = models.ForeignKey(AffiliateProfile, on_delete=models.CASCADE, related_name="commissions")
    link = models.ForeignKey(AffiliateLink, on_delete=models.CASCADE, related_name="commissions")
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="affiliate_commission")
    amount = models.DecimalField(_("montant de la commission (FCFA)"), max_digits=10, decimal_places=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("commission d'affiliation")
        verbose_name_plural = _("commissions d'affiliation")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commission {self.affiliate} — {self.amount} FCFA"
