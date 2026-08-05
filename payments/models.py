import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import Course


class PaymentProvider(models.TextChoices):
    # Contrat direct avec chaque opérateur — voir payments/providers/ pour
    # l'implémentation de chacun. Orange Money et Wave s'appuient sur une
    # documentation publique officielle (voir commentaires dans leurs
    # modules respectifs) ; Moov Money et Coris Money n'ont pas de doc
    # publique trouvée et doivent être complétés une fois le contrat signé.
    ORANGE_MONEY = "orange_money", _("Orange Money")
    MOOV_MONEY = "moov_money", _("Moov Money")
    WAVE = "wave", _("Wave")
    CORIS_MONEY = "coris_money", _("Coris Money")
    # PayDunya reste disponible en option (agrégateur, une seule intégration
    # technique) si un contrat direct s'avère trop long à obtenir.
    PAYDUNYA = "paydunya", _("PayDunya (agrégateur, en secours)")


class SubscriptionPlan(models.Model):
    """Formule d'abonnement (mensuel, trimestriel, annuel)."""

    class Period(models.TextChoices):
        MONTHLY = "monthly", _("Mensuel")
        QUARTERLY = "quarterly", _("Trimestriel")
        YEARLY = "yearly", _("Annuel")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("nom"), max_length=150)
    period = models.CharField(max_length=20, choices=Period.choices)
    price = models.DecimalField(_("prix (FCFA)"), max_digits=10, decimal_places=0)
    duration_days = models.PositiveIntegerField(_("durée en jours"))
    description = models.TextField(blank=True)
    gives_full_catalog_access = models.BooleanField(
        default=True, help_text=_("Donne accès à tout le catalogue plutôt qu'à un cours précis")
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("formule d'abonnement")
        verbose_name_plural = _("formules d'abonnement")
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} ({self.get_period_display()}) — {self.price} FCFA"


class Subscription(models.Model):
    """Abonnement actif ou passé d'un étudiant."""

    class Status(models.TextChoices):
        ACTIVE = "active", _("Actif")
        EXPIRED = "expired", _("Expiré")
        CANCELLED = "cancelled", _("Annulé")
        PENDING = "pending", _("En attente de paiement")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("abonnement")
        verbose_name_plural = _("abonnements")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} — {self.plan} ({self.status})"


class Payment(models.Model):
    """Transaction de paiement : achat de cours ou abonnement, via mobile money."""

    class Status(models.TextChoices):
        PENDING = "pending", _("En attente")
        PROCESSING = "processing", _("En cours de traitement")
        SUCCESS = "success", _("Réussi")
        FAILED = "failed", _("Échoué")
        CANCELLED = "cancelled", _("Annulé")
        REFUNDED = "refunded", _("Remboursé")

    class PurposeType(models.TextChoices):
        COURSE_PURCHASE = "course_purchase", _("Achat de cours")
        SUBSCRIPTION = "subscription", _("Abonnement")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(_("référence interne"), max_length=64, unique=True, db_index=True)

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    purpose = models.CharField(max_length=20, choices=PurposeType.choices)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")

    provider = models.CharField(_("opérateur"), max_length=20, choices=PaymentProvider.choices)
    payer_phone_number = models.CharField(_("numéro payeur"), max_length=20, blank=True)
    amount = models.DecimalField(_("montant (FCFA)"), max_digits=10, decimal_places=0)
    currency = models.CharField(max_length=10, default="XOF")

    # Champs de rapprochement avec l'API de l'opérateur mobile money (ou de
    # l'agrégateur PayDunya).
    provider_transaction_id = models.CharField(_("ID transaction opérateur"), max_length=128, blank=True)
    provider_response_payload = models.JSONField(_("réponse brute de l'opérateur"), default=dict, blank=True)
    checkout_url = models.URLField(
        _("URL de paiement hébergée"), blank=True,
        help_text=_("Page PayDunya vers laquelle rediriger le client pour payer."),
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    failure_reason = models.CharField(max_length=255, blank=True)

    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("paiement")
        verbose_name_plural = _("paiements")
        ordering = ["-initiated_at"]
        indexes = [
            models.Index(fields=["status", "provider"]),
            models.Index(fields=["student"]),
        ]

    def __str__(self):
        return f"{self.reference} — {self.amount} FCFA ({self.get_status_display()})"


class InstructorPayout(models.Model):
    """Reversement des revenus à un formateur (déduction faite de la commission plateforme)."""

    class Status(models.TextChoices):
        PENDING = "pending", _("En attente")
        PROCESSING = "processing", _("En cours")
        PAID = "paid", _("Payé")
        FAILED = "failed", _("Échoué")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payouts")
    period_start = models.DateField()
    period_end = models.DateField()
    gross_amount = models.DecimalField(_("montant brut (FCFA)"), max_digits=12, decimal_places=0)
    platform_commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    net_amount = models.DecimalField(_("montant net (FCFA)"), max_digits=12, decimal_places=0)
    provider = models.CharField(max_length=20, choices=PaymentProvider.choices, blank=True)
    payout_phone_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("reversement formateur")
        verbose_name_plural = _("reversements formateurs")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reversement {self.instructor} — {self.net_amount} FCFA"
