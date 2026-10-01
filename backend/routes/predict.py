"""
predict.py — Disease prediction route with optional auth and DB persistence.
"""

from flask import Blueprint, request, jsonify, g
from database.health_db import save_history
from ai.human_health_engine import HumanHealthEngine
from ai.animal_health_engine import AnimalHealthEngine
from routes.auth import optional_auth

predict_bp = Blueprint("predict", __name__)
human_engine = HumanHealthEngine()
animal_engine = AnimalHealthEngine()


@predict_bp.route("/predict", methods=["POST"])
@optional_auth
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request payload required"}), 400

        domain   = data.get("domain", "human")
        text     = data.get("text", "")
        symptoms = data.get("symptoms", [])
        severity = data.get("severity", "")
        history  = data.get("history", "")
        species  = data.get("species", "")
        user_id  = getattr(g, "user_id", None)

        if domain == "animal":
            result = animal_engine.assess(text, symptoms=symptoms, severity=severity,
                                          species=species, history=history)
        else:
            result = human_engine.assess(text, symptoms=symptoms, severity=severity,
                                         history=history)

        save_history({
            "user_id":  user_id,
            "domain":   domain,
            "symptoms": symptoms or [text],
            "disease":  result.get("disease", ""),
            "confidence": result.get("confidence", 0),
            "risk_level": result.get("risk_level", "low"),
            "emergency":  result.get("emergency", False),
            "doctor_type": result.get("doctor_type", ""),
            "additional_info": {"source": "predict_api", "severity": severity, "species": species},
        })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500
