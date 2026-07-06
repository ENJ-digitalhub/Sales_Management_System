# backend/utils/validators.py
VALID_PAYMENT_METHODS = {"cash", "transfer", "pos"}


def validate_sale_payload(data):
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

        if not isinstance(product_id, str) or not product_id:
            return {"valid": False, "error": f"Invalid product_id at index {idx}"}

        if product_id in seen_product_ids:
            return {"valid": False, "error": f"Duplicate product_id: {product_id}"}
        seen_product_ids.add(product_id)

        if not isinstance(quantity, int) or quantity <= 0:
            return {"valid": False, "error": f"Quantity must be positive for product {product_id}"}

        validated_items.append({"product_id": product_id, "quantity": quantity})

    if payment_method not in VALID_PAYMENT_METHODS:
        return {"valid": False, "error": "Invalid payment method"}

    return {
        "valid": True,
        "error": None,
        "items": validated_items,
        "payment_method": payment_method,
    }