from typing import Any, Dict, List, Optional

from ai.disease_predictor import DiseasePredictor
from ai.emergency_detector import EmergencyDetector
from ai.medicine_recommender import MedicineRecommender
from ai.risk_calculator import RiskCalculator
from services.knowledge_service import find_disease


class AnimalHealthEngine:
    def __init__(self):
        self.predictor = DiseasePredictor()
        self.emergency_detector = EmergencyDetector()
        self.medicine_recommender = MedicineRecommender()
        self.risk_calculator = RiskCalculator()

    def assess(
        self,
        text: str,
        symptoms: Optional[List[str]] = None,
        severity: str = "",
        species: str = "animal",
        history: str = "",
    ) -> Dict[str, Any]:
        symptom_input = symptoms or []
        if not symptom_input:
            symptom_input = [text]

        predictions = self.predictor.predict(symptom_input, domain="animal", top_n=3)
        primary = predictions[0]
        emergency = self.emergency_detector.detect(text, symptom_input)
        risk = self.risk_calculator.calculate(primary.get("risk_level", "medium"), severity, emergency["emergency"])
        medicine_details = self.medicine_recommender.recommend(primary["disease_name"], domain="animal")
        disease_data = find_disease(primary["disease_name"], domain="animal") or {}

        return {
            "disease": primary["disease_name"],
            "confidence": primary["confidence"],
            "risk_level": risk["risk_level"],
            "risk_reason": risk["reason"],
            "description": primary.get("description", ""),
            "symptoms": primary.get("symptoms", []),
            "causes": primary.get("causes", []),
            "precautions": primary.get("precautions", []),
            "medicines": [m["name"] for m in medicine_details],
            "medicine_details": medicine_details,
            "diet": primary.get("diet", []),
            "recommended_tests": primary.get("recommended_tests", []),
            "home_remedies": primary.get("home_remedies", []),
            "doctor_type": primary.get("doctor_type", "Veterinarian"),
            "emergency": emergency["emergency"],
            "emergency_warnings": emergency["warnings"],
            "disclaimer": "Consult a licensed veterinarian for accurate diagnosis.",
            "body_system": primary.get("body_system", "Veterinary"),
            "source": "knowledge_base",
            "species": species,
            "history": history,
            "related_conditions": [p["disease_name"] for p in predictions[1:3]],
            "medication_notes": [m.get("notes", "") for m in medicine_details],
            "raw_prediction": predictions,
            "disease_data": disease_data,
        }
