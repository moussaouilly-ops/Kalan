"""Adaptateur PayDunya — conserve la même interface que les opérateurs directs."""

from .base import BaseProviderAdapter, InitiateResult, ProviderError, WebhookResult
from ..paydunya import PayDunyaError, create_checkout_invoice, verify_ipn_hash


class PayDunyaAdapter(BaseProviderAdapter):
    def initiate(self, *, amount, reference, description, callback_url, phone_number=None) -> InitiateResult:
        try:
            checkout_url, invoice_token = create_checkout_invoice(
                amount=amount, description=description, store_name="Kàlan", callback_url=callback_url,
                custom_data={"payment_reference": reference},
            )
        except PayDunyaError as e:
            raise ProviderError(str(e))
        return InitiateResult(checkout_url=checkout_url, provider_reference=invoice_token, raw_response={})

    def parse_webhook(self, request) -> WebhookResult:
        payload = request.data.get("data", request.data)
        if not verify_ipn_hash(payload.get("hash", "")):
            raise ProviderError("Hash de vérification PayDunya invalide.")
        invoice = payload.get("invoice", {})
        custom_data = payload.get("custom_data", {})
        pd_status = payload.get("status")
        status = "success" if pd_status == "completed" else ("cancelled" if pd_status == "cancelled" else "failed")
        return WebhookResult(
            provider_reference=custom_data.get("payment_reference") or invoice.get("token", ""),
            status=status,
            raw_payload=payload,
            failure_reason=payload.get("fail_reason", ""),
        )
