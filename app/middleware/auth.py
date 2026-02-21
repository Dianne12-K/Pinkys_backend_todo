from functools import wraps
from flask import jsonify, request, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User


def auth_required(fn):
    """Decorator to protect routes. Injects current_user into flask.g."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user:
                return jsonify({"error": "User not found"}), 401
            g.current_user = user
        except Exception as e:
            return jsonify({"error": "Unauthorized", "detail": str(e)}), 401
        return fn(*args, **kwargs)
    return wrapper


def register_middleware(app):
    """Register app-level before/after request hooks."""

    @app.before_request
    def log_request():
        app.logger.debug(f"--> {request.method} {request.path}")

    @app.after_request
    def add_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Route not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500