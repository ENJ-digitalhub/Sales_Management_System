# backend/utils/validators.py
VALID_PAYMENT_METHODS = {"cash", "transfer", "pos"}

def validate_sale_payload(data, require_transaction_id=True):
    if not isinstance(data, dict):
        return {"valid": False, "error": "Invalid payload format"}

    items = data.get("items")
    payment_method = data.get("payment_method")

    if not items or not isinstance(items, list):
        return {"valid": False, "error": "Items must be a non-empty list"}

    seen_product_ids = set()
    validated_items = []

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            return {"valid": False, "error": f"Invalid item format at index {idx}"}

        product_id = item.get("product_id")
        quantity = item.get("quantity")

        if not isinstance(product_id, int):
            return {"valid": False, "error": f"Invalid product_id at index {idx}"}

        if product_id in seen_product_ids:
            return {"valid": False, "error": f"Duplicate product_id: {product_id}"}

        seen_product_ids.add(product_id)

        if not isinstance(quantity, int) or quantity <= 0:
            return {"valid": False, "error": f"Quantity must be positive for product {product_id}"}

        validated_items.append({
            "product_id": product_id,
            "quantity": quantity
        })

    if payment_method not in VALID_PAYMENT_METHODS:
        return {"valid": False, "error": "Invalid payment method"}

    payment_provider = data.get("payment_provider")
    payment_details = data.get("payment_details")
    device_id = data.get("device_id")
    client_transaction_id = data.get("client_transaction_id")

    if payment_provider and not isinstance(payment_provider, str):
        return {"valid": False, "error": "payment_provider must be a string"}

    if payment_details and not isinstance(payment_details, (dict, list)):
        return {"valid": False, "error": "payment_details must be an object or list"}

    if device_id and not isinstance(device_id, str):
        return {"valid": False, "error": "device_id must be a string"}

    if require_transaction_id:
        if not client_transaction_id:
            return {"valid": False, "error": "client_transaction_id is required"}
        if not device_id:
            return {"valid": False, "error": "device_id is required"}

    return {
        "valid": True,
        "error": None,
        "items": validated_items,
        "payment_method": payment_method,
        "payment_provider": payment_provider,
        "payment_details": payment_details,
        "device_id": device_id,
        "client_transaction_id": client_transaction_id,
    }