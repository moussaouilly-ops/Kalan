"""
Adaptateur Orange Money — API Web Payment / M Payment officielle.

Documentation : https://developer.orange.com/apis/om-webpay

⚠️ IMPORTANT : au moment de l'écriture de ce code, la documentation
officielle liste les pays couverts par cette API comme étant le Mali, le
Cameroun, la Côte d'Ivoire, le Sénégal, Madagascar, le Botswana, la Guinée
Conakry, la Guinée Bissau, la Sierra Leone, la RD Congo et la République
Centrafricaine — LE BURKINA FASO N'Y FIGURE PAS EXPLICITEMENT.
Il est probable qu'Orange Money Burkina Faso utilise une API locale
différente. Cet adaptateur est écrit sur la base de la documentation
officielle du groupe Orange (la mieux documentée publiquement) comme point
de départ solide, mais DOIT être vérifié/ajusté avec Orange Money Burkina
Faso S.A. une fois le contrat signé (ils indiqueront le bon country_code,
et confirmeront si c'est bien cette API ou une autre).

Fonctionnement :
1. Authentification OAuth2 (client_credentials) pour obtenir un jeton Bearer.
2. Création d'un paiement web (POST .../v1/webpayment), qui renvoie une URL
   de paiement (payment_url) vers laquelle rediriger le client.
3. Le client génère un code OTP via *144# sur son téléphone et le saisit sur
   la page Orange Money pour valider.
4. Orange notifie ensuite notre `notif_url` (webhook).
"""

from django.conf import settings

import requests

from .base import BaseProviderAdapter, InitiateResult, ProviderError, WebhookResult

OAUTH_TOKEN_URL = "https://api.orange.com/oauth/v3/token"


class OrangeMoneyAdapter(BaseProviderAdapter):
    def _get_access_token(self):
        config = settings.MOBILE_MONEY_PROVIDERS["orange_money"]
        response = requests.post(
            OAUTH_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {config['auth_header']}"},
            timeout=15,
        )
        data = response.json()
        if "access_token" not in data:
            raise ProviderError(f"Échec d'authentification Orange Money : {data}")
        return data["access_token"]

    def initiate(self, *, amount, reference, description, callback_url, phone_number=None) -> InitiateResult:
        config = settings.MOBILE_MONEY_PROVIDERS["orange_money"]
        if not config.get("auth_header") or not config.get("merchant_key"):
            raise ProviderError(
                "Clés Orange Money non configurées — renseigne ORANGE_MONEY_AUTH_HEADER et "
                "ORANGE_MONEY_MERCHANT_KEY dans .env (voir developer.orange.com après souscription)."
            )

        token = self._get_access_token()
        country_code = config.get("country_code", "bf")  # "bf" à confirmer avec Orange Money Burkina Faso
        base_url = "https://api.orange.com/orange-money-webpay"
        # En développement (DEBUG=True), utilise l'environnement sandbox
        # d'Orange ("dev"). En production, utilise le country_code réel
        # (ex: "bf") confirmé par Orange Money Burkina Faso.
        env = "dev" if settings.DEBUG else country_code
        url = f"{base_url}/{env}/v1/webpayment"

        payload = {
            "merchant_key": config["merchant_key"],
            "currency": "OUV",  # code devise Orange Money pour XOF, à reconfirmer
            "order_id": reference,
            "amount": int(amount),
            "return_url": callback_url,
            "cancel_url": callback_url,
            "notif_url": callback_url,
            "lang": "fr",
            "reference": description,
        }
        response = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
        data = response.json()

        if "payment_url" not in data:
            raise ProviderError(f"Échec de création du paiement Orange Money : {data}")

        return InitiateResult(
            checkout_url=data["payment_url"],
            provider_reference=data.get("pay_token", reference),
            raw_response=data,
        )

    def parse_webhook(self, request) -> WebhookResult:
        # ⚠️ Format à confirmer avec la documentation fournie lors de la
        # souscription — non standardisé publiquement pour cette étape.
        payload = request.data
        status_raw = payload.get("status", "").upper()
        status = "success" if status_raw == "SUCCESS" else "failed"
        return WebhookResult(
            provider_reference=payload.get("order_id", ""),
            status=status,
            raw_payload=payload,
        )
