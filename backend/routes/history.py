"""
history.py — History routes with real database integration and dashboard stats.
"""

from flask import Blueprint, jsonify, g
from database.health_db import get_history, get_history_item, get_history_stats
from routes.auth import optional_auth

history_bp = Blueprint("history", __name__)


@history_bp.route("/history", methods=["GET"])
@optional_auth
def get_history_route():
    try:
        user_id = getattr(g, "user_id", None)
        history = get_history(limit=100, user_id=user_id)
        stats = get_history_stats(user_id=user_id)
        return jsonify({"history": history, "stats": stats})
    except Exception as e:
        return jsonify({"error": f"Failed to fetch history: {str(e)}"}), 500


@history_bp.route("/history/stats", methods=["GET"])
@optional_auth
def get_stats():
    try:
        user_id = getattr(g, "user_id", None)
        stats = get_history_stats(user_id=user_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch stats: {str(e)}"}), 500


@history_bp.route("/history/<history_id>", methods=["GET"])
@optional_auth
def get_history_item_route(history_id):
    try:
        item = get_history_item(history_id)
        if not item:
            return jsonify({"error": "History item not found"}), 404
        return jsonify(item)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch history item: {str(e)}"}), 500
