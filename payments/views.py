import uuid
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course, Enrollment
from .models import InstructorPayout, Payment, PaymentProvider, Subscription, SubscriptionPlan
from .providers.base import ProviderError
from .providers.registry import get_adapter
from .serializers import (
    InitiatePaymentSerializer,
    InstructorPayoutSerializer,
    PaymentSerializer,
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
)


class SubscriptionPlanListView(generics.ListAPIView):
    """GET /api/v1/payments/plans/ — formules d'abonnement actives (public)."""

    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class InitiatePaymentView(APIView):
    """
    POST /api/v1/payments/initiate/ — crée la transaction côté plateforme,
    puis appelle l'API réelle de l'opérateur choisi (`provider`) via son
    adaptateur dédié (voir payments/providers/). La réponse contient
    `checkout_url` si l'opérateur fonctionne par redirection (Orange Money,
    Wave) — le frontend doit alors rediriger le client dessus pour qu'il
    termine son paiement.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "payment_initiate"

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payment_kwargs = dict(
            reference=f"KLN-{uuid.uuid4().hex[:12].upper()}",
            student=request.user,
            purpose=data["purpose"],
            provider=data["provider"],
            status=Payment.Status.PENDING,
        )

        description = ""
        if data["purpose"] == Payment.PurposeType.COURSE_PURCHASE:
            course = get_object_or_404(Course, id=data["course"], status=Course.Status.PUBLISHED)
            if Enrollment.objects.filter(student=request.user, course=course, is_active=True).exists():
                return Response({"detail": "Vous êtes déjà inscrit à ce cours."}, status=400)
            payment_kwargs["course"] = course
            payment_kwargs["amount"] = course.effective_price
            description = f"Inscription au cours « {course.title} »"
        else:
            plan = get_object_or_404(SubscriptionPlan, id=data["plan"], is_active=True)
            subscription = Subscription.objects.create(
                student=request.user, plan=plan, status=Subscription.Status.PENDING
            )
            payment_kwargs["subscription"] = subscription
            payment_kwargs["amount"] = plan.price
            description = f"Abonnement Kàlan — {plan.name}"

        payment = Payment.objects.create(**payment_kwargs)

        callback_url = request.build_absolute_uri(
            reverse("payments:webhook", kwargs={"provider": data["provider"]})
        )
        try:
            adapter = get_adapter(data["provider"])
            result = adapter.initiate(
                amount=payment.amount,
                reference=payment.reference,
                description=description,
                callback_url=callback_url,
            )
        except ProviderError as e:
            payment.status = Payment.Status.FAILED
            payment.failure_reason = str(e)
            payment.save(update_fields=["status", "failure_reason"])
            return Response({"detail": str(e)}, status=502)
        except Exception:
            payment.status = Payment.Status.FAILED
            payment.failure_reason = "Erreur inattendue lors de l'appel à l'opérateur."
            payment.save(update_fields=["status", "failure_reason"])
            return Response(
                {"detail": "Impossible de contacter l'opérateur choisi. Vérifie ta connexion et la configuration."},
                status=502,
            )

        payment.provider_transaction_id = result.provider_reference
        payment.checkout_url = result.checkout_url or ""
        payment.provider_response_payload = result.raw_response
        payment.status = Payment.Status.PROCESSING
        payment.save(update_fields=[
            "provider_transaction_id", "checkout_url", "provider_response_payload", "status",
        ])

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentWebhookView(APIView):
    """
    POST /api/v1/payments/webhook/<provider>/ — notification envoyée par
    l'opérateur pour confirmer (ou signaler l'échec d') une transaction.
    Chaque opérateur ayant son propre format, on délègue le décodage à
    l'adaptateur concerné (`parse_webhook`), puis on applique un traitement
    commun (mise à jour du statut, activation de l'accès si succès).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, provider):
        try:
            adapter = get_adapter(provider)
            result = adapter.parse_webhook(request)
        except ProviderError as e:
            return Response({"detail": str(e)}, status=400)
        except Exception:
            return Response({"detail": "Impossible de traiter la notification."}, status=400)

        payment = Payment.objects.filter(
            provider=provider, provider_transaction_id=result.provider_reference,
        ).first()
        if payment is None:
            # Repli : certains opérateurs renvoient notre référence interne
            # plutôt que la leur selon le champ utilisé.
            payment = Payment.objects.filter(reference=result.provider_reference).first()
        if payment is None:
            return Response({"detail": "Transaction introuvable."}, status=404)

        payment.provider_response_payload = result.raw_payload

        if result.status == "success":
            payment.status = Payment.Status.SUCCESS
            payment.completed_at = timezone.now()
            self._fulfill(payment)
        elif result.status == "cancelled":
            payment.status = Payment.Status.CANCELLED
        elif result.status == "pending":
            payment.status = Payment.Status.PROCESSING
        else:
            payment.status = Payment.Status.FAILED
            payment.failure_reason = result.failure_reason or "Échec signalé par l'opérateur."

        payment.save()
        return Response({"detail": "Webhook traité."})

    def _fulfill(self, payment):
        """Active l'accès (inscription ou abonnement) après paiement réussi."""
        if payment.purpose == Payment.PurposeType.COURSE_PURCHASE and payment.course:
            Enrollment.objects.get_or_create(
                student=payment.student, course=payment.course,
                defaults={"source": Enrollment.Source.PURCHASE},
            )
        elif payment.purpose == Payment.PurposeType.SUBSCRIPTION and payment.subscription:
            sub = payment.subscription
            sub.status = Subscription.Status.ACTIVE
            sub.starts_at = timezone.now()
            sub.ends_at = timezone.now() + timedelta(days=sub.plan.duration_days)
            sub.save()


class MyPaymentsView(generics.ListAPIView):
    """GET /api/v1/payments/my-payments/ — historique des paiements de l'étudiant connecté."""

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(student=self.request.user)


class MySubscriptionsView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(student=self.request.user)


class MyPayoutsView(generics.ListAPIView):
    """GET /api/v1/payments/my-payouts/ — reversements du formateur connecté."""

    serializer_class = InstructorPayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InstructorPayout.objects.filter(instructor=self.request.user)
