"""
auth.py — Real authentication with SQLite + bcrypt + JWT
"""

import re
import os
import jwt
import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from database.health_db import (
    create_user, get_user_by_email, get_user_by_id,
    update_last_login, update_user_profile,
    add_token_blacklist, is_token_blacklisted,
)

auth_bp = Blueprint("auth", __name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "ai-health-secret-change-in-production-2024")
TOKEN_EXPIRY_DAYS = 7


# ── Helpers ────────────────────────────────────────────────────────────────────

def generate_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=TOKEN_EXPIRY_DAYS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


def validate_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))


# ── Auth middleware decorators ─────────────────────────────────────────────────

def require_auth(f):
    """Decorator — verifies JWT, checks blacklist, sets g.user_id."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        try:
            payload = decode_token(token)
            # Task 15: reject blacklisted (logged-out) tokens
            if is_token_blacklisted(token):
                return jsonify({"error": "Token has been revoked. Please log in again."}), 401
            g.user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


def optional_auth(f):
    """Decorator — sets g.user_id if token present and valid, else None."""
    @wraps(f)
    def decorated(*args, **kwargs):
        g.user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                if not is_token_blacklisted(token):
                    payload = decode_token(token)
                    g.user_id = payload["user_id"]
            except Exception:
                pass
        return f(*args, **kwargs)
    return decorated


# ── Routes ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        name     = (data.get("name") or "").strip()
        email    = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not name or len(name) < 2:
            return jsonify({"error": "Name must be at least 2 characters"}), 400
        if not email or not validate_email(email):
            return jsonify({"error": "Invalid email address"}), 400
        if not password or len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        if get_user_by_email(email):
            return jsonify({"error": "An account with this email already exists"}), 409

        password_hash = generate_password_hash(password)
        user_id = create_user(name, email, password_hash)
        token   = generate_token(user_id)

        return jsonify({
            "message": "Account created successfully",
            "user":    {"id": user_id, "name": name, "email": email},
            "token":   token,
        }), 201

    except Exception as e:
        return jsonify({"error": f"Signup failed: {str(e)}"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        email    = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid email or password"}), 401

        update_last_login(user["id"])
        token = generate_token(user["id"])

        return jsonify({
            "message": "Login successful",
            "user":    {"id": user["id"], "name": user["name"], "email": user["email"]},
            "token":   token,
        })

    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    """Task 15: blacklist the current token so it cannot be reused."""
    try:
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.split(" ", 1)[1] if auth_header.startswith("Bearer ") else ""
        if token:
            payload = decode_token(token)
            exp = payload.get("exp", 0)
            add_token_blacklist(token, exp)
        return jsonify({"message": "Logged out successfully"})
    except Exception as e:
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500


@auth_bp.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    try:
        user = get_user_by_id(g.user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user)
    except Exception as e:
        return jsonify({"error": f"Failed to get profile: {str(e)}"}), 500


@auth_bp.route("/profile", methods=["PUT"])
@require_auth
def update_profile():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        user = get_user_by_id(g.user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        name = (data.get("name") or "").strip()
        if not name or len(name) < 2:
            return jsonify({"error": "Name must be at least 2 characters"}), 400

        new_password = data.get("new_password", "")
        if new_password:
            current_password = data.get("current_password", "")
            full_user = get_user_by_email(user["email"])
            if not full_user or not check_password_hash(full_user["password_hash"], current_password):
                return jsonify({"error": "Current password is incorrect"}), 401
            if len(new_password) < 6:
                return jsonify({"error": "New password must be at least 6 characters"}), 400
            update_user_profile(g.user_id, name, generate_password_hash(new_password))
        else:
            update_user_profile(g.user_id, name, None)

        updated = get_user_by_id(g.user_id)
        return jsonify({"message": "Profile updated", "user": updated})
    except Exception as e:
        return jsonify({"error": f"Update failed: {str(e)}"}), 500


@auth_bp.route("/verify", methods=["GET"])
@require_auth
def verify_token():
    """Quick token validity check."""
    return jsonify({"valid": True, "user_id": g.user_id})
