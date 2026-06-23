from flask import request, jsonify
from backend.services.auth_service import AuthService

def login_controller():
    """Handles the request/response processing lifecycle for user authentication."""
    body = request.get_json()
    if not body:
        return jsonify({"error": "Missing request body"}), 400
        
    username = body.get("username")
    password = body.get("password")
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Temporary user object placeholder matching modern 2.0 properties for Phase 2 testing
    class FakeUser:
        id = 1
        role = "admin"
        
    token = AuthService.issue_token(FakeUser)
    return jsonify({"token": token}), 200