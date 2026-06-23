from flask import request, jsonify
from backend.services.auth_service import AuthService

def login_controller():
    """Handles the incoming request/response payload lifecycle for user logins."""
    body = request.get_json()
    if not body:
        return jsonify({"error": "Missing valid JSON request body"}), 400
        
    username = body.get("username")
    password = body.get("password")
    
    if not username or not password:
        return jsonify({"error": "Username and password fields are strictly required"}), 400

    # Delegate authentication operation to the service layer
    token = AuthService.authenticate_user(username, password)
    if not token:
        return jsonify({"error": "Invalid username or password credentials"}), 401
        
    return jsonify({"token": token}), 200

def me_controller():
    """Extracts identity context from request object claims data."""
    # Context injected by your secure custom middleware decorator
    claims = getattr(request, "user_claims", {})
    user_id = claims.get("sub")
    
    if not user_id:
        return jsonify({"error": "Identity identification context lost"}), 400
        
    # Delegate data lookup to the service layer
    profile = AuthService.get_profile_data(user_id)
    if not profile:
        return jsonify({"error": "User profile records not found"}), 404
        
    return jsonify(profile), 200