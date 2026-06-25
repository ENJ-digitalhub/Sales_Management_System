# backend/utils/validators.py
def validate_pagination_params(page_str, per_page_str):
    """Validates and sanitizes query arguments safely."""
    try:
        page = max(int(page_str), 1) if page_str else 1
        per_page = min(max(int(per_page_str), 1), 100) if per_page_str else 20
        return {"page": page, "per_page": per_page, "error": None}
    except ValueError:
        return {"page": None, "per_page": None, "error": "Pagination parameters must be integers"}