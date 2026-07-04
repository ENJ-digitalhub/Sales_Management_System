# Compatibility shim — re-exports from the canonical auth middleware location.
# backend/utils/auth_middleware.py is the real implementation.
from backend.utils.auth_middleware import require_auth, require_role

__all__ = ['require_auth', 'require_role']
