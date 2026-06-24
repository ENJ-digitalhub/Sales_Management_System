from flask import Blueprint
from backend.controllers.auth_controller import AuthController
from backend.utils.auth_decorators import login_required

# Create the Blueprint with the required prefix
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Bind public login endpoint to controller
auth_bp.route('/login', methods=['POST'])(AuthController.login)

# Bind protected profile endpoint to controller using custom middleware
auth_bp.route('/me', methods=['GET'])(login_required(AuthController.get_me))