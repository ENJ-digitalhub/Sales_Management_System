from decimal import Decimal
from datetime import date, datetime as dt, timedelta

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
    # --- Phase 4 additions ---

ALLOWED_PRODUCT_FIELDS = {"name", "category", "selling_price", "cost_price", "stock_quantity"}


def validate_product_payload(payload: dict, partial: bool = False):
    """
    partial=False (create): name, selling_price, cost_price, stock_quantity are required.
    partial=True (edit/PATCH): all fields optional, but at least one must be present,
    and any field present must still pass the same value checks.
    """
    if not isinstance(payload, dict):
        return {"valid": False, "error": "Invalid payload"}

    if partial:
        provided = {k: v for k, v in payload.items() if k in ALLOWED_PRODUCT_FIELDS}
        if not provided:
            return {"valid": False, "error": "No valid fields provided to update"}
    else:
        required = {"name", "selling_price", "cost_price", "stock_quantity"}
        missing = required - payload.keys()
        if missing:
            return {"valid": False, "error": f"Missing required fields: {', '.join(sorted(missing))}"}
        provided = {k: v for k, v in payload.items() if k in ALLOWED_PRODUCT_FIELDS}

    if "name" in provided:
        if not isinstance(provided["name"], str) or not provided["name"].strip():
            return {"valid": False, "error": "name must be a non-empty string"}

    if "category" in provided and provided["category"] is not None:
        if not isinstance(provided["category"], str):
            return {"valid": False, "error": "category must be a string"}

    for field in ("selling_price", "cost_price"):
        if field in provided:
            try:
                value = float(provided[field])
            except (TypeError, ValueError):
                return {"valid": False, "error": f"{field} must be a number"}
            if value < 0:
                return {"valid": False, "error": f"{field} cannot be negative"}

    if "stock_quantity" in provided:
        try:
            qty = int(provided["stock_quantity"])
        except (TypeError, ValueError):
            return {"valid": False, "error": "stock_quantity must be an integer"}
        if qty < 0:
            return {"valid": False, "error": "stock_quantity cannot be negative"}
        provided["stock_quantity"] = qty

    return {"valid": True, "fields": provided}


def validate_purchase_payload(payload: dict):
    if not isinstance(payload, dict):
        return {"valid": False, "error": "Invalid payload"}

    items = payload.get("items")
    supplier = payload.get("supplier")

    if not items or not isinstance(items, list):
        return {"valid": False, "error": "items must be a non-empty list"}

    if supplier is not None and not isinstance(supplier, str):
        return {"valid": False, "error": "supplier must be a string"}

    normalized = []
    for it in items:
        if not isinstance(it, dict):
            return {"valid": False, "error": "Each item must be an object"}

        pid = it.get("product_id")
        qty = it.get("quantity")
        cost = it.get("cost_price")

        if not pid or not isinstance(pid, str):
            return {"valid": False, "error": "product_id missing or invalid"}

        try:
            q = int(qty)
        except (TypeError, ValueError):
            return {"valid": False, "error": "quantity must be an integer"}
        if q <= 0:
            return {"valid": False, "error": "quantity must be positive"}

        try:
            c = float(cost)
        except (TypeError, ValueError):
            return {"valid": False, "error": "cost_price must be a number"}
        if c < 0:
            return {"valid": False, "error": "cost_price cannot be negative"}

        normalized.append({"product_id": pid, "quantity": q, "cost_price": c})

    return {"valid": True, "items": normalized, "supplier": supplier}


def validate_daily_report_params(date_param):
    """Defaults to today if not provided. Expects YYYY-MM-DD."""
    if not date_param:
        return {"valid": True, "date": date.today()}
    try:
        parsed = dt.strptime(date_param, "%Y-%m-%d").date()
        return {"valid": True, "date": parsed}
    except ValueError:
        return {"valid": False, "error": "date must be in YYYY-MM-DD format"}


def validate_monthly_report_params(month_param):
    """Defaults to current month if not provided. Expects YYYY-MM."""
    if not month_param:
        today = date.today()
        return {"valid": True, "year": today.year, "month": today.month}
    try:
        parsed = dt.strptime(month_param, "%Y-%m")
        return {"valid": True, "year": parsed.year, "month": parsed.month}
    except ValueError:
        return {"valid": False, "error": "month must be in YYYY-MM format"}


def validate_yearly_report_params(year_param):
    """Defaults to current year if not provided. Expects YYYY."""
    if not year_param:
        return {"valid": True, "year": date.today().year}
    try:
        year = int(year_param)
        if year < 2000 or year > 2100:
            return {"valid": False, "error": "year out of reasonable range"}
        return {"valid": True, "year": year}
    except ValueError:
        return {"valid": False, "error": "year must be a valid integer"}


def validate_employee_report_params(from_param, to_param):
    """
    Both optional. If neither given, defaults to the last 30 days.
    If given, both must be valid YYYY-MM-DD and from <= to.
    """
    if not from_param and not to_param:
        today = date.today()
        from_date = today - timedelta(days=30)
        return {"valid": True, "from_date": from_date, "to_date": today}

    try:
        from_date = dt.strptime(from_param, "%Y-%m-%d").date() if from_param else None
        to_date = dt.strptime(to_param, "%Y-%m-%d").date() if to_param else None
    except ValueError:
        return {"valid": False, "error": "from/to must be in YYYY-MM-DD format"}

    if from_date is None:
        from_date = to_date
    if to_date is None:
        to_date = date.today()

    if from_date > to_date:
        return {"valid": False, "error": "from date must be before or equal to to date"}

    return {"valid": True, "from_date": from_date, "to_date": to_date}