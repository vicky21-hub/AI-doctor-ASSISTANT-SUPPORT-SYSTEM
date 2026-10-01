"""
disease_predictor.py — Advanced disease prediction with ranked alternatives.

Flow:
  raw symptoms (list or string)
    → spell correction
    → expand_text() NLP normalization
    → SymptomMatcher.match() TF-IDF + keyword overlap + RapidFuzz
    → weighted confidence scoring with symptom overlap boost
    → context-aware adjustments (age, gender, symptom count, risk level)
    → rank top 3 diseases with DIFFERENT confidence scores
    → never return "General Discomfort" — indicate needs_more_info instead

Rules:
  - Single symptom like "fever" alone → low confidence, needs more info
  - High-risk diseases penalised when symptom count < 3
  - 2nd prediction gets -8 pts, 3rd gets -15 pts for diversity
"""

import logging
from typing import Any, Dict, List, Optional, Union

from ai.symptom_matcher import (
    SymptomMatcher, expand_text, correct_spelling,
    fuzzy_match_disease_name, get_symptoms_from_disease_name,
)
from services.knowledge_service import find_disease, get_diseases

logger = logging.getLogger(__name__)

MIN_CONFIDENCE = 8
HIGH_CONFIDENCE_THRESHOLD = 50


# ── Symptom overlap boost ──────────────────────────────────────────────────────

def _symptom_overlap_boost(user_symptoms: List[str], disease: Dict[str, Any]) -> float:
    if not user_symptoms:
        return 0.0
    disease_symptoms = {s.lower() for s in disease.get("symptoms", [])}
    user_lower = {s.lower() for s in user_symptoms}
    if not disease_symptoms:
        return 0.0

    direct  = len(user_lower & disease_symptoms)
    partial = sum(
        1 for us in user_lower for ds in disease_symptoms
        if us != ds and (us in ds or ds in us)
    )
    total = max(1, len(disease_symptoms))
    boost = (direct * 2.0 + partial * 0.5) / (total * 2.0)
    return min(boost, 0.50)


# ── Context-aware confidence adjustments ──────────────────────────────────────

def _apply_context_adjustments(
    disease: Dict[str, Any],
    confidence: float,
    user_symptoms: List[str],
    patient_context: Optional[Dict[str, Any]] = None,
) -> float:
    adj = 0.0

    disease_symptoms = {s.lower() for s in disease.get("symptoms", [])}
    user_lower = {s.lower() for s in user_symptoms}
    matching  = len(user_lower & disease_symptoms)
    total_sym = max(1, len(user_symptoms))
    risk_level = disease.get("risk_level", "medium").lower()

    # Fewer symptoms than disease profile → reduce confidence
    if total_sym < 3 and len(disease_symptoms) >= 5:
        adj -= 0.15
    elif matching >= 3:
        adj += 0.10

    # High-risk diseases need more supporting evidence
    if risk_level == "high":
        if total_sym < 3:
            adj -= 0.20
        elif matching < 2:
            adj -= 0.15

    # Patient context boosts
    if patient_context:
        age = patient_context.get("age")
        medical_history = patient_context.get("medical_history", [])
        if age and age > 60 and risk_level == "high":
            adj += 0.05
        for item in medical_history:
            if item.lower() in disease.get("description", "").lower():
                adj += 0.08

    return max(0.0, min(95.0, confidence + adj * 100))


# ── DiseasePredictor class ─────────────────────────────────────────────────────

class DiseasePredictor:
    def __init__(self):
        self.matcher = SymptomMatcher()

    def predict(
        self,
        symptoms: Union[str, List[str]],
        domain: str = "human",
        top_n: int = 3,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if isinstance(symptoms, list):
            raw_query   = " ".join(symptoms)
            symptom_list = symptoms
        else:
            raw_query    = symptoms or ""
            symptom_list = [raw_query]

        # ── Direct disease-name fuzzy lookup ──────────────────────────────────
        all_names = [d["disease_name"] for d in get_diseases(domain)]
        direct_match, direct_score = fuzzy_match_disease_name(
            raw_query, all_names, threshold=65
        )

        predictions: List[Dict[str, Any]] = []

        if direct_match and direct_score >= 65:
            disease = find_disease(direct_match, domain=domain)
            if disease:
                conf = min(90, int(40 + (direct_score - 65) * 1.0))
                logger.info(
                    "[DiseasePredictor] direct name match: %r → %s (fuzzy=%d, conf=%d)",
                    raw_query, direct_match, direct_score, conf,
                )
                predictions.append(self._build_prediction(disease, conf, patient_context, symptom_list))

        # ── TF-IDF path ───────────────────────────────────────────────────────
        tfidf = self._run_tfidf(
            raw_query, symptom_list, domain, top_n,
            skip=direct_match if direct_match else None,
            patient_context=patient_context,
        )

        if direct_match:
            predictions.extend(tfidf[: top_n - 1])
        else:
            predictions = tfidf[:top_n]

        # ── Fallback ──────────────────────────────────────────────────────────
        if not predictions or predictions[0].get("disease_name") == "needs_more_info":
            logger.warning("[DiseasePredictor] insufficient info for %r", raw_query)
            return [{
                "disease_name":      "needs_more_info",
                "confidence":        0,
                "description":       "The symptoms provided are not yet sufficient for a reliable assessment.",
                "symptoms":          [],
                "causes":            [],
                "precautions":       ["Rest and monitor symptoms", "Stay hydrated", "Avoid self-medication"],
                "medicines":         [],
                "supplements":       [],
                "diet":              ["Light meals", "Plenty of fluids"],
                "risk_level":        "low",
                "doctor_type":       "General Physician",
                "recommended_tests": [],
                "home_remedies":     ["Rest", "Stay hydrated"],
                "body_system":       "General",
                "emergency":         False,
                "red_flags":         [],
                "recovery_advice":   "Please describe your symptoms in more detail, including when they started and how long they have lasted.",
            }]

        logger.info(
            "[DiseasePredictor] final: %s",
            [(p["disease_name"], p["confidence"]) for p in predictions[:top_n]],
        )
        return predictions[:top_n]

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _build_prediction(
        self,
        disease: Dict[str, Any],
        confidence: int,
        patient_context: Optional[Dict[str, Any]] = None,
        user_symptoms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Single authoritative _build_prediction — context-aware."""
        if user_symptoms:
            confidence = int(_apply_context_adjustments(
                disease, float(confidence), user_symptoms, patient_context
            ))

        return {
            "disease_name":      disease.get("disease_name", "Unknown"),
            "confidence":        max(0, min(100, confidence)),
            "description":       disease.get("description", ""),
            "symptoms":          disease.get("symptoms", []),
            "causes":            disease.get("causes", []),
            "precautions":       disease.get("precautions", []),
            "medicines":         disease.get("medicines", []),
            "supplements":       disease.get("supplements", []),
            "diet":              disease.get("diet", []),
            "risk_level":        disease.get("risk_level", "medium"),
            "doctor_type":       disease.get("doctor_type", "General Physician"),
            "recommended_tests": disease.get("recommended_tests", []),
            "home_remedies":     disease.get("home_remedies", []),
            "body_system":       disease.get("body_system", "General"),
            "emergency":         bool(disease.get("emergency", False)),
            "red_flags":         disease.get("red_flags", []),       # fixed: was using emergency flag
            "recovery_advice":   disease.get("recovery_advice", ""),
        }

    def _run_tfidf(
        self,
        raw_query: str,
        symptom_list: List[str],
        domain: str,
        top_n: int,
        skip: str = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        corrected = correct_spelling(raw_query)
        expanded  = expand_text(corrected)

        logger.debug(
            "[DiseasePredictor] raw=%r corrected=%r expanded=%r domain=%s",
            raw_query, corrected, expanded, domain,
        )

        matches = self.matcher.match(expanded, domain=domain, top_n=top_n * 4)
        if not matches and len(symptom_list) > 1:
            matches = self.matcher.search_symptoms(symptom_list, domain=domain)

        predictions: List[Dict[str, Any]] = []
        seen: set = {skip} if skip else set()

        for name, score in matches:
            if name in seen:
                continue
            seen.add(name)

            disease = find_disease(name, domain=domain)
            if not disease:
                continue

            conf = int(score * 100) + int(_symptom_overlap_boost(symptom_list, disease) * 100)
            conf = int(_apply_context_adjustments(disease, float(conf), symptom_list, patient_context))
            conf = min(95, conf)

            if conf < MIN_CONFIDENCE:
                continue

            # Enforce diversity: reduce 2nd/3rd predictions
            rank = len(predictions)
            if rank == 1:
                conf = max(MIN_CONFIDENCE, conf - 8)
            elif rank == 2:
                conf = max(MIN_CONFIDENCE, conf - 15)

            predictions.append(self._build_prediction(disease, conf, patient_context, symptom_list))

            if len(predictions) >= top_n:
                break

        logger.info(
            "[DiseasePredictor] tfidf %r → %s",
            raw_query,
            [(p["disease_name"], p["confidence"]) for p in predictions],
        )
        return predictions

    def needs_more_info(self, predictions: List[Dict[str, Any]]) -> bool:
        if not predictions:
            return True
        top = predictions[0]
        return top["disease_name"] == "needs_more_info" or top["confidence"] < HIGH_CONFIDENCE_THRESHOLD

    def get_differential_diagnoses(self, predictions: List[Dict[str, Any]]) -> List[str]:
        return [p["disease_name"] for p in predictions[1:] if p["disease_name"] != "needs_more_info"]

    def get_top_conditions_summary(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not predictions or predictions[0]["disease_name"] == "needs_more_info":
            return {
                "status": "insufficient_info",
                "message": "Need more information about your symptoms",
                "next_steps": ["Describe symptoms in more detail", "Answer diagnostic questions"],
            }
        return {
            "status": "analysis_complete",
            "top_conditions": [
                {
                    "rank":       i + 1,
                    "name":       p["disease_name"],
                    "confidence": p["confidence"],
                    "risk_level": p["risk_level"],
                    "emergency":  p["emergency"],
                    "doctor_type": p["doctor_type"],
                }
                for i, p in enumerate(predictions[:3])
            ],
            "recommendation": (
                "See recommended specialist" if predictions[0]["confidence"] >= 70
                else "Consult a healthcare provider for definitive diagnosis"
            ),
        }
