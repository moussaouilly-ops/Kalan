from rest_framework import serializers

from .models import InstructorPayout, Payment, PaymentProvider, Subscription, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ["id", "name", "period", "price", "duration_days", "description", "gives_full_catalog_access"]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_detail = SubscriptionPlanSerializer(source="plan", read_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "plan", "plan_detail", "status", "starts_at", "ends_at", "auto_renew", "created_at"]
        read_only_fields = ["status", "starts_at", "ends_at", "created_at"]


class InitiatePaymentSerializer(serializers.Serializer):
    """
    Corps de requête pour démarrer un paiement mobile money.
    purpose='course_purchase' -> fournir 'course'
    purpose='subscription'    -> fournir 'plan'
    Le client (front-end) doit demander à l'utilisateur de choisir son
    opérateur AVANT d'appeler cet endpoint, puisque chaque opérateur a son
    propre contrat et sa propre API.
    """

    purpose = serializers.ChoiceField(choices=Payment.PurposeType.choices)
    provider = serializers.ChoiceField(choices=PaymentProvider.choices)
    course = serializers.UUIDField(required=False)
    plan = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if attrs["purpose"] == Payment.PurposeType.COURSE_PURCHASE and not attrs.get("course"):
            raise serializers.ValidationError({"course": "Requis pour un achat de cours."})
        if attrs["purpose"] == Payment.PurposeType.SUBSCRIPTION and not attrs.get("plan"):
            raise serializers.ValidationError({"plan": "Requis pour un abonnement."})
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "reference", "purpose", "course", "subscription", "provider",
            "payer_phone_number", "amount", "currency", "status", "checkout_url",
            "failure_reason", "initiated_at", "completed_at",
        ]
        read_only_fields = fields


class InstructorPayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorPayout
        fields = [
            "id", "period_start", "period_end", "gross_amount",
            "platform_commission_percent", "net_amount", "provider",
            "payout_phone_number", "status", "processed_at", "created_at",
        ]
        read_only_fields = fields
