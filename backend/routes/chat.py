"""
chat.py — AI chat route with enhanced medical reasoning.
Stages: greeting → asking_severity → asking_duration → asking_history → diagnosis

Uses EnhancedAIDoctorEngine for:
  - Disease-specific question flows
  - Input validation
  - Conversation memory
  - Medical reasoning with differential diagnosis
  - Detailed doctor reports
  - Real doctor-like behavior
"""

from flask import Blueprint, request, jsonify, g
from services.enhanced_ai_doctor_engine import EnhancedAIDoctorEngine
from database.health_db import save_history
from routes.auth import optional_auth
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)
engine = EnhancedAIDoctorEngine()

MAX_MESSAGE_LENGTH = 2000


@chat_bp.route("/chat", methods=["POST"])
@optional_auth
def chat():
    """
    Process user message through enhanced AI Doctor consultation system.

    Request JSON:
    {
        "message": "User's message",
        "state": {... previous conversation state}
    }

    Response JSON:
    {
        "reply": "AI response",
        "state": {...conversation state},
        "emergency": bool,
        "is_diagnosis": bool
    }
    """
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400

        message = data.get("message", "").strip()
        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Task 14: input length cap
        if len(message) > MAX_MESSAGE_LENGTH:
            return jsonify({"error": f"Message too long. Maximum {MAX_MESSAGE_LENGTH} characters."}), 400

        state = data.get("state", {})

        # Process through enhanced engine
        result = engine.process_message(message, state)

        user_id = getattr(g, "user_id", None)
        logger.info(f"Consultation for user {user_id}: stage={result['state'].get('current_stage')}")

        # Task 3: persist completed diagnosis to history
        if result.get("is_diagnosis"):
            s = result.get("state", {})
            symptoms = list(dict.fromkeys(s.get("symptoms", []) + s.get("extra_symptoms", [])))
            disease = s.get("primary_diagnosis") or ""
            confidence = s.get("confidence", 0)
            emergency = result.get("emergency", False)
            risk_level = "high" if emergency else ("medium" if confidence < 70 else "low")
            try:
                save_history({
                    "user_id":     user_id,
                    "domain":      "human",
                    "symptoms":    symptoms,
                    "disease":     disease,
                    "confidence":  confidence,
                    "risk_level":  risk_level,
                    "emergency":   emergency,
                    "doctor_type": "",
                    "additional_info": {"source": "chat"},
                })
            except Exception as save_err:
                logger.warning(f"Failed to save chat history: {save_err}")

        return jsonify({
            "reply": result["reply"],
            "state": result["state"],
            "emergency": result.get("emergency", False),
            "is_diagnosis": result.get("is_diagnosis", False),
        })

    except Exception as e:
        logger.exception(f"Chat processing error: {str(e)}")
        return jsonify({"error": f"Chat processing failed: {str(e)}"}), 500
