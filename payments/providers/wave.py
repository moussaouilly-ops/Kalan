"""
Adaptateur Wave — API Checkout officielle.

Documentation : https://docs.wave.com/checkout
Webhooks       : https://docs.wave.com/webhook

Fonctionnement (confirmé par la documentation publique) :
1. POST /v1/checkout/sessions avec amount, currency, success_url, error_url.
2. Wave renvoie un objet "Checkout Session" contenant `wave_launch_url` :
   c'est l'URL vers laquelle rediriger le client pour qu'il paie.
3. Une fois payé, Wave envoie un webhook de type
   "checkout.session.completed" avec le statut du paiement.

Il faut créer une clé API sur business.wave.com (section Developers), après
avoir vérifié son identité (CNI + registre de commerce). Compter 48-72h de
validation.
"""

from django.conf import settings

import requests

from .base import BaseProviderAdapter, InitiateResult, ProviderError, WebhookResult

WAVE_BASE_URL = "https://api.wave.com/v1"


class WaveAdapter(BaseProviderAdapter):
    def initiate(self, *, amount, reference, description, callback_url, phone_number=None) -> InitiateResult:
        config = settings.MOBILE_MONEY_PROVIDERS["wave"]
        if not config.get("api_key"):
            raise ProviderError(
                "Clé API Wave non configurée — renseigne WAVE_API_KEY dans .env "
                "(business.wave.com → Developers)."
            )

        payload = {
            "amount": str(int(amount)),
            "currency": "XOF",
            "success_url": callback_url,
            "error_url": callback_url,
            "client_reference": reference,
        }
        response = requests.post(
            f"{WAVE_BASE_URL}/checkout/sessions",
            json=payload,
            headers={
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        data = response.json()

        if "wave_launch_url" not in data:
            raise ProviderError(f"Échec de création de la session Wave : {data}")

        return InitiateResult(
            checkout_url=data["wave_launch_url"],
            provider_reference=data["id"],  # identifiant "cos-..."
            raw_response=data,
        )

    def parse_webhook(self, request) -> WebhookResult:
        payload = request.data
        data = payload.get("data", {})
        event_type = payload.get("type", "")

        if event_type != "checkout.session.completed":
            return WebhookResult(provider_reference=data.get("id", ""), status="pending", raw_payload=payload)

        payment_status = data.get("payment_status")
        status = "success" if payment_status == "succeeded" else "failed"
        return WebhookResult(
            provider_reference=data.get("id", ""),
            status=status,
            raw_payload=payload,
            failure_reason=data.get("last_payment_error") or "",
        )
