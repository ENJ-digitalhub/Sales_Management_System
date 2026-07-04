from decimal import Decimal

ALLOWED_PAYMENT_METHODS = {
    "cash",
    "card",
    "contactless",
    "bank_transfer",
    "ussd",
    "qr_payment",
    "pos_terminal",
    "digital_wallet",
    "store_wallet",
    "credit_sale",
    "installment",
    "gift_card",
    "loyalty_points",
    "split_payment",
    "trexave_pay",
    "other",
}

SUPPORTED_PAYMENT_PROVIDERS = {
    "paystack",
    "flutterwave",
    "moniepoint",
    "opay",
    "palmpay",
    "kuda",
    "gtbank",
    "access",
    "uba",
    "zenith",
    "firstbank",
    "fcmb",
    "fidelity",
    "sterling",
    "wema",
    "providus",
    "custom",
}

PROVIDER_REQUIRED_METHODS = {
    "card",
    "contactless",
    "bank_transfer",
    "digital_wallet",
    "store_wallet",
    "ussd",
    "qr_payment",
    "pos_terminal",
    "trexave_pay",
    "other",
}

SPLIT_METHOD = "split_payment"


def validate_sale_payload(payload: dict, require_transaction_id: bool = False):
    """
    require_transaction_id=True for sale creation (needs device_id +
    client_transaction_id for offline idempotency). False for edits,
    which operate on an existing sale_id and don't need these.
    """
    if not isinstance(payload, dict):
        return {"valid": False, "error": "Invalid payload"}

    items = payload.get("items")
    payment_method = payload.get("payment_method")
    payment_provider = payload.get("payment_provider")
    payment_details = payload.get("payment_details")
    device_id = payload.get("device_id")
    client_transaction_id = payload.get("client_transaction_id")

    if require_transaction_id:
        if not device_id or not isinstance(device_id, str):
            return {"valid": False, "error": "device_id is required"}
        if not client_transaction_id or not isinstance(client_transaction_id, str):
            return {"valid": False, "error": "client_transaction_id is required"}

    if not items or not isinstance(items, list):
        return {"valid": False, "error": "Items must be a non-empty list"}

    if payment_method not in ALLOWED_PAYMENT_METHODS:
        return {"valid": False, "error": "Invalid payment_method"}

    if payment_method == SPLIT_METHOD:
        if not isinstance(payment_details, list) or len(payment_details) == 0:
            return {"valid": False, "error": "payment_details is required for split_payment"}
        if payment_provider is not None:
            return {"valid": False, "error": "payment_provider must not be set for split_payment"}
    else:
        if payment_method in PROVIDER_REQUIRED_METHODS and not payment_provider:
            return {"valid": False, "error": f"payment_provider is required for {payment_method}"}
        if payment_provider is not None and payment_provider not in SUPPORTED_PAYMENT_PROVIDERS:
            return {"valid": False, "error": "Invalid payment_provider"}

    seen = set()
    normalized = []

    for it in items:
        if not isinstance(it, dict):
            return {"valid": False, "error": "Each item must be an object"}

        pid = it.get("product_id")
        qty = it.get("quantity")

        if not pid or not isinstance(pid, str):
            return {"valid": False, "error": "product_id missing or invalid"}

        try:
            q = int(qty)
        except Exception:
            return {"valid": False, "error": "Quantity must be integer"}

        if q <= 0:
            return {"valid": False, "error": "Quantities must be positive integers"}

        if pid in seen:
            return {"valid": False, "error": "Duplicate product_id in payload; aggregate quantities before sending"}

        seen.add(pid)
        normalized.append({"product_id": pid, "quantity": q})

    if payment_method == SPLIT_METHOD:
        for part in payment_details:
            if not isinstance(part, dict):
                return {"valid": False, "error": "Each payment detail must be an object"}

            part_method = part.get("method")
            part_provider = part.get("provider")
            amount = part.get("amount")

            if part_method not in ALLOWED_PAYMENT_METHODS - {SPLIT_METHOD}:
                return {"valid": False, "error": "Invalid split payment method"}

            if part_method in PROVIDER_REQUIRED_METHODS and not part_provider:
                return {"valid": False, "error": f"provider is required for split payment method {part_method}"}

            if part_provider is not None and part_provider not in SUPPORTED_PAYMENT_PROVIDERS:
                return {"valid": False, "error": "Invalid split payment provider"}

            try:
                amt = Decimal(str(amount))
            except Exception:
                return {"valid": False, "error": "Invalid split payment amount"}

            if amt <= 0:
                return {"valid": False, "error": "Split payment amounts must be positive"}

        return {
            "valid": True,
            "items": normalized,
            "payment_method": payment_method,
            "payment_provider": None,
            "payment_details": payment_details,
            "device_id": device_id,
            "client_transaction_id": client_transaction_id,
        }

    return {
        "valid": True,
        "items": normalized,
        "payment_method": payment_method,
        "payment_provider": payment_provider,
        "payment_details": None,
        "device_id": device_id,
        "client_transaction_id": client_transaction_id,
    }


def validate_pagination_params(page_param, per_page_param):
    try:
        page = int(page_param) if page_param else 1
        per_page = int(per_page_param) if per_page_param else 10
        if page < 1 or per_page < 1:
            raise ValueError
        return {"error": None, "page": page, "per_page": per_page}
    except Exception:
        return {"error": "Invalid pagination parameters", "page": None, "per_page": None}