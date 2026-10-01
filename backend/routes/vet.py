"""
vet.py — Veterinary AI chat route with optional auth.
"""

from flask import Blueprint, request, jsonify, g
from database.health_db import save_history
from ai.animal_health_engine import AnimalHealthEngine
from routes.auth import optional_auth

vet_bp = Blueprint("vet", __name__)
vet_engine = AnimalHealthEngine()


@vet_bp.route("/vet/chat", methods=["POST"])
@optional_auth
def vet_chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request payload required"}), 400

        text     = data.get("message", "")
        symptoms = data.get("symptoms", [])
        severity = data.get("severity", "")
        species  = data.get("species", "animal")
        history  = data.get("history", "")
        user_id  = getattr(g, "user_id", None)

        result = vet_engine.assess(text, symptoms=symptoms, severity=severity,
                                   species=species, history=history)

        save_history({
            "user_id":  user_id,
            "domain":   "animal",
            "symptoms": symptoms or [text],
            "disease":  result.get("disease", ""),
            "confidence": result.get("confidence", 0),
            "risk_level": result.get("risk_level", "low"),
            "emergency":  result.get("emergency", False),
            "doctor_type": result.get("doctor_type", "Veterinarian"),
            "additional_info": {"source": "vet_chat", "species": species},
        })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Veterinary chat failed: {str(e)}"}), 500
