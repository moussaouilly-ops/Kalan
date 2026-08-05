"""
Adaptateur Coris Money.

⚠️ Aucune documentation d'API publique trouvée pour un contrat marchand
direct avec Coris Money au moment de l'écriture de ce code. Comme pour Moov
Money, contacte Coris Money directement (c'est un produit de Coris Bank
International) pour connaître leurs modalités d'intégration technique.

Marche à suivre une fois le contrat signé : identique à moov_money.py —
adapter `initiate()` et `parse_webhook()` avec le format réel qu'ils
fournissent dans leur documentation d'intégration.
"""

from django.conf import settings

from .base import BaseProviderAdapter, InitiateResult, ProviderError, WebhookResult


class CorisMoneyAdapter(BaseProviderAdapter):
    def initiate(self, *, amount, reference, description, callback_url, phone_number=None) -> InitiateResult:
        config = settings.MOBILE_MONEY_PROVIDERS["coris_money"]
        if not config.get("base_url") or not config.get("merchant_key"):
            raise ProviderError(
                "Intégration Coris Money non configurée. Aucune documentation publique "
                "n'a pu être trouvée pour ce fournisseur — contacte Coris Bank "
                "International pour obtenir leurs identifiants marchands et leur "
                "documentation technique, puis complète "
                "payments/providers/coris_money.py avec le format d'appel réel."
            )
        raise ProviderError("Adaptateur Coris Money non implémenté — voir TODO dans ce fichier.")

    def parse_webhook(self, request) -> WebhookResult:
        raise ProviderError("Format de webhook Coris Money non implémenté — voir TODO dans ce fichier.")
