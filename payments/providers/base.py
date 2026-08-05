"""
Interface commune à tous les adaptateurs de paiement mobile money.

Chaque opérateur (Orange Money, Moov Money, Wave, Coris Money) a son propre
format d'API. Pour que le reste du code (vues, webhook) n'ait pas à connaître
ces différences, chaque adaptateur expose la même interface : `initiate()`
et `parse_webhook()`.
"""

from dataclasses import dataclass
from typing import Optional


class ProviderError(Exception):
    """Levée quand un opérateur refuse ou échoue à démarrer un paiement."""


@dataclass
class InitiateResult:
    # URL vers laquelle rediriger le client pour qu'il termine son paiement
    # (Orange Money, Wave). Peut être None si l'opérateur pousse directement
    # une notification sur le téléphone du client sans redirection (flux
    # USSD "push" pur — à confirmer selon la doc réelle de chaque opérateur).
    checkout_url: Optional[str]
    # Identifiant de la transaction côté opérateur, à conserver pour
    # retrouver le paiement quand le webhook arrive.
    provider_reference: str
    # Réponse brute, utile pour le débogage et l'audit.
    raw_response: dict


@dataclass
class WebhookResult:
    provider_reference: str
    status: str  # "success" | "failed" | "cancelled" | "pending"
    raw_payload: dict
    failure_reason: str = ""


class BaseProviderAdapter:
    """À sous-classer par chaque opérateur."""

    def initiate(self, *, amount, reference, description, callback_url, phone_number=None) -> InitiateResult:
        raise NotImplementedError

    def parse_webhook(self, request) -> WebhookResult:
        raise NotImplementedError
