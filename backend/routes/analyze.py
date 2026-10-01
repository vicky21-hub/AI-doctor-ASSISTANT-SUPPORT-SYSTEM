"""
analyze.py — Text/symptom analysis route with optional auth.
"""

from flask import Blueprint, request, jsonify, g
from ai.human_health_engine import HumanHealthEngine
from ai.animal_health_engine import AnimalHealthEngine
from database.health_db import save_history
from routes.auth import optional_auth

analyze_bp = Blueprint("analyze", __name__)
human_engine = HumanHealthEngine()
animal_engine = AnimalHealthEngine()


@analyze_bp.route("/analyze", methods=["POST"])
@optional_auth
def analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Analysis data required"}), 400

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
            "additional_info": {"source": "analyze_api", "severity": severity, "species": species},
        })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500
