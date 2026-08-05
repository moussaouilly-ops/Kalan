"""
Intégration PayDunya (agrégateur de paiement mobile money : Orange Money
Burkina Faso, Moov Burkina Faso, Wave, carte bancaire).

Documentation officielle : https://developers.paydunya.com/doc/FR/softpay

Fonctionnement retenu ici : le mode "Checkout Invoice" — le plus simple à
intégrer et le plus robuste. On crée une facture via l'API, PayDunya renvoie
une URL de paiement hébergée, on redirige le client dessus. Le client choisit
lui-même son opérateur (Orange Money, Moov Money, Wave...) sur cette page.
PayDunya notifie ensuite notre backend via un webhook (IPN).

Pour un contrôle plus fin de l'interface (rester sur notre propre site plutôt
que rediriger), PayDunya propose aussi l'API SoftPay par opérateur — plus
complexe (gestion des codes OTP dans notre propre UI), à envisager plus tard
une fois le volume de transactions suffisant pour le justifier.
"""

import hashlib

import requests
from django.conf import settings

PAYDUNYA_BASE_URL = "https://app.paydunya.com/api/v1"


class PayDunyaError(Exception):
    """Levée quand PayDunya refuse ou échoue à créer la facture de paiement."""


def _headers():
    keys = settings.PAYDUNYA
    return {
        "Content-Type": "application/json",
        "PAYDUNYA-MASTER-KEY": keys["master_key"],
        "PAYDUNYA-PRIVATE-KEY": keys["private_key"],
        "PAYDUNYA-TOKEN": keys["token"],
    }


def create_checkout_invoice(*, amount, description, store_name, callback_url, custom_data=None):
    """
    Crée une facture de paiement PayDunya et renvoie l'URL de paiement
    hébergée vers laquelle rediriger le client, ainsi que le jeton de facture
    (utile pour retrouver la transaction plus tard).

    Retourne : (checkout_url: str, invoice_token: str)
    Lève PayDunyaError en cas d'échec (ex: clés API absentes/invalides).
    """
    payload = {
        "invoice": {
            "total_amount": int(amount),
            "description": description,
        },
        "store": {
            "name": store_name,
        },
        "actions": {
            "callback_url": callback_url,
        },
    }
    if custom_data:
        payload["custom_data"] = custom_data

    response = requests.post(
        f"{PAYDUNYA_BASE_URL}/checkout-invoice/create",
        json=payload,
        headers=_headers(),
        timeout=15,
    )
    data = response.json()

    if data.get("response_code") != "00":
        raise PayDunyaError(data.get("response_text", "Échec de création de la facture PayDunya."))

    return data["response_text"], data["token"]


def verify_ipn_hash(received_hash):
    """
    PayDunya renvoie, dans son webhook (IPN), un hash SHA-512 de notre clé
    maîtresse (Master Key) — cela permet de vérifier que la notification
    provient bien de PayDunya et pas d'un tiers malveillant qui imiterait
    l'appel. À utiliser sur CHAQUE webhook reçu avant de faire confiance à
    son contenu.
    """
    expected = hashlib.sha512(settings.PAYDUNYA["master_key"].encode()).hexdigest()
    return received_hash == expected
