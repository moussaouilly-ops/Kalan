"""
Adaptateur Moov Money.

⚠️ Aucune documentation d'API publique trouvée pour un contrat marchand
direct avec Moov Money Burkina Faso au moment de l'écriture de ce code.
Contrairement à Orange Money et Wave (documentation publique officielle),
Moov Money fournit généralement sa documentation d'intégration
uniquement après signature du contrat marchand.

Marche à suivre une fois le contrat signé :
1. Moov Money te remettra un identifiant marchand + des clés API, et un
   document technique décrivant les endpoints (souvent une API REST avec
   un flux "push USSD" : le client reçoit une notification sur son
   téléphone à valider avec son code secret).
2. Adapter `initiate()` ci-dessous pour appeler leur endpoint réel.
3. Adapter `parse_webhook()` selon le format de notification qu'ils
   utilisent (certains opérateurs utilisent des callbacks HTTP simples,
   d'autres des formats plus proches de webhooks JSON standards).
"""

from django.conf import settings

from .base import BaseProviderAdapter, InitiateResult, ProviderError, WebhookResult


class MoovMoneyAdapter(BaseProviderAdapter):
    def initiate(self, *, amount, reference, description, callback_url, phone_number=None) -> InitiateResult:
        config = settings.MOBILE_MONEY_PROVIDERS["moov_money"]
        if not config.get("base_url") or not config.get("merchant_key"):
            raise ProviderError(
                "Intégration Moov Money non configurée. Aucune documentation publique "
                "n'a pu être trouvée pour ce fournisseur — contacte Moov Money Burkina "
                "Faso pour obtenir leurs identifiants marchands et leur documentation "
                "technique, puis complète payments/providers/moov_money.py avec le "
                "format d'appel réel qu'ils fournissent."
            )
        # TODO : remplacer par le vrai format d'appel une fois la doc obtenue.
        raise ProviderError("Adaptateur Moov Money non implémenté — voir TODO dans ce fichier.")

    def parse_webhook(self, request) -> WebhookResult:
        raise ProviderError("Format de webhook Moov Money non implémenté — voir TODO dans ce fichier.")
