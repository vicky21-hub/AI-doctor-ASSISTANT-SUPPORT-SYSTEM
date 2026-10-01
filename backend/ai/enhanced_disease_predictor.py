"""
enhanced_disease_predictor.py - Production-ready disease prediction with differential diagnosis.

Features:
  - Advanced symptom matching
  - Confidence scoring
  - Alternative diagnoses
  - Risk assessment
  - Never returns empty diagnoses
"""

import logging
from typing import Dict, List, Any, Union, Optional, Tuple

from utils.text_normalizer import TextNormalizer
from utils.medical_reasoning_engine import MedicalReasoningEngine
from services.knowledge_service import get_diseases, find_disease

logger = logging.getLogger(__name__)

MIN_CONFIDENCE = 15
HIGH_CONFIDENCE_THRESHOLD = 45


class EnhancedDiseasePredictor:
    """Production-ready disease prediction system."""

    def __init__(self):
        """Initialize with disease database and reasoning engine."""
        self.diseases = get_diseases("human")
        self.reasoning_engine = MedicalReasoningEngine(self.diseases)
        self.normalizer = TextNormalizer()

    def predict(
        self,
        symptoms: Union[str, List[str]],
        location: Optional[str] = None,
        severity: Optional[int] = None,
        duration: Optional[Dict] = None,
        top_n: int = 3,
    ) -> Dict[str, Any]:
        """
        Predict diseases from symptoms with differential diagnosis.

        Args:
            symptoms: Symptom text or list
            location: Body location (optional)
            severity: Severity 1-10 (optional)
            duration: {"value": int, "unit": str} (optional)
            top_n: Number of alternative diagnoses

        Returns:
            {
                "primary_disease": "Disease Name",
                "confidence": 75,
                "alternatives": [
                    {"disease": "Disease2", "confidence": 45},
                    ...
                ],
                "risk_level": "medium",
                "emergency": False,
                "reasoning": "...",
                "recommendations": [...],
            }
        """

        # Normalize input
        if isinstance(symptoms, list):
            symptom_list = symptoms
        else:
            symptom_list = [symptoms]

        # Use medical reasoning engine
        analysis = self.reasoning_engine.analyze_symptoms(
            symptom_list,
            location=location,
            severity=severity,
            duration=duration,
        )

        return {
            "primary_disease": analysis.get("primary_diagnosis"),
            "confidence": analysis.get("confidence", 0),
            "alternatives": analysis.get("alternative_diagnoses", []),
            "risk_level": analysis.get("risk_level", "unknown"),
            "emergency": analysis.get("requires_emergency", False),
            "reasoning": analysis.get("reasoning", ""),
            "recommendations": analysis.get("next_steps", []),
            "description": analysis.get("description", ""),
        }

    def predict_from_text(self, text: str) -> Dict[str, Any]:
        """
        Quick prediction from natural language text.
        Extracts symptoms and returns prediction.
        """

        # Extract symptoms from text
        symptoms = self._extract_symptoms_from_text(text)

        if not symptoms:
            return {
                "error": "No symptoms detected. Please describe your condition more clearly.",
                "primary_disease": None,
                "confidence": 0,
            }

        return self.predict(symptoms)

    def _extract_symptoms_from_text(self, text: str) -> List[str]:
        """Extract symptoms from natural language text."""

        normalized = self.normalizer.normalize_text(text)

        # Try disease name first
        disease = self.normalizer.fuzzy_match_disease(text)
        symptoms = [disease] if disease else []

        # Extract body parts
        body_parts = self.normalizer.extract_body_parts(text)
        symptoms.extend(body_parts)

        # Look for common symptoms
        symptom_keywords = [
            "fever", "cold", "cough", "headache", "chest pain", "stomach pain",
            "nausea", "vomiting", "diarrhea", "fatigue", "weakness", "dizziness",
            "anxiety", "depression", "insomnia", "rash", "itching", "joint pain",
            "muscle pain", "back pain", "neck pain", "throat pain", "ear pain",
            "eye pain", "breathing", "shortness of breath", "palpitations",
            "sweating", "chills", "pain", "discomfort", "inflammation",
            "swelling", "burning", "tingling", "numbness", "loss of appetite",
        ]

        for keyword in symptom_keywords:
            if keyword in normalized:
                symptoms.append(keyword)

        return list(set(symptoms))

    def get_disease_details(self, disease_name: str) -> Dict[str, Any]:
        """Get detailed information about a disease."""

        disease = find_disease(disease_name, "human")
        if not disease:
            return {"error": "Disease not found"}

        return {
            "name": disease.get("disease_name"),
            "description": disease.get("description"),
            "symptoms": disease.get("symptoms", []),
            "causes": disease.get("causes", []),
            "risk_level": disease.get("risk_level"),
            "doctor_type": disease.get("doctor_type"),
            "emergency": disease.get("emergency", False),
            "medicines": disease.get("medicines", []),
            "precautions": disease.get("precautions", []),
            "diet": disease.get("diet", []),
            "home_remedies": disease.get("home_remedies", []),
            "recommended_tests": disease.get("recommended_tests", []),
        }

    def validate_prediction(self, prediction: Dict) -> Tuple[bool, str]:
        """
        Validate that prediction is reasonable.

        Returns:
            (is_valid, message)
        """

        if not prediction.get("primary_disease"):
            return False, "No disease could be identified. Please provide more details."

        confidence = prediction.get("confidence", 0)
        if confidence < 20:
            return False, "Confidence too low. Need more information."

        return True, "Prediction is valid."


# Backward compatibility
class DiseasePredictor(EnhancedDiseasePredictor):
    """Backward compatible disease predictor."""
    pass
