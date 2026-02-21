from flask import Blueprint, request, g
from flask_jwt_extended import create_access_token
from app.extensions import db, bcrypt
from app.models import User
from app.middleware.auth import auth_required
from app.utils.helpers import success, error

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    """
    Register a new user.
    ---
    tags:
      - Auth
    security: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/definitions/RegisterRequest'
    responses:
      201:
        description: User created successfully
        content:
          application/json:
            schema:
              $ref: '#/definitions/AuthResponse'
      400:
        description: Missing required fields
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
      409:
        description: Email or username already taken
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json() or {}
    if not all([data.get("email"), data.get("username"), data.get("password")]):
        return error("email, username, and password are required")
    if User.query.filter_by(email=data["email"]).first():
        return error("Email already registered", 409)
    if User.query.filter_by(username=data["username"]).first():
        return error("Username already taken", 409)

    hashed = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user = User(email=data["email"], username=data["username"], password_hash=hashed)
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=user.id)
    return success({"user": user.to_dict(), "token": token}, "Registered successfully", 201)


@auth_bp.post("/login")
def login():
    """
    Login and receive a JWT token.
    ---
    tags:
      - Auth
    security: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/definitions/LoginRequest'
    responses:
      200:
        description: Login successful
        content:
          application/json:
            schema:
              $ref: '#/definitions/AuthResponse'
      401:
        description: Invalid credentials
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get("email")).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, data.get("password", "")):
        return error("Invalid email or password", 401)
    token = create_access_token(identity=user.id)
    return success({"user": user.to_dict(), "token": token}, "Login successful")


@auth_bp.get("/me")
@auth_required
def me():
    """
    Get the currently authenticated user.
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    responses:
      200:
        description: Current user
        content:
          application/json:
            schema:
              $ref: '#/definitions/UserResponse'
      401:
        description: Unauthorized
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    return success(g.current_user.to_dict())