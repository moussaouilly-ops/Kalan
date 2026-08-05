"""Registre central des adaptateurs de paiement, par code opérateur."""

from .coris_money import CorisMoneyAdapter
from .moov_money import MoovMoneyAdapter
from .orange_money import OrangeMoneyAdapter
from .paydunya_adapter import PayDunyaAdapter
from .wave import WaveAdapter

ADAPTERS = {
    "orange_money": OrangeMoneyAdapter(),
    "moov_money": MoovMoneyAdapter(),
    "wave": WaveAdapter(),
    "coris_money": CorisMoneyAdapter(),
    "paydunya": PayDunyaAdapter(),
}


def get_adapter(provider_code):
    adapter = ADAPTERS.get(provider_code)
    if adapter is None:
        raise ValueError(f"Opérateur inconnu : {provider_code}")
    return adapter
