"""
medical_reasoning_engine.py - Advanced medical reasoning with differential diagnosis.

Features:
  - Symptom analysis and matching
  - Differential diagnosis generation
  - Confidence scoring
  - Risk level assessment
  - Alternative diagnosis ranking
"""

from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class MedicalReasoningEngine:
    """Generate medical reasoning and differential diagnosis."""

    def __init__(self, disease_db: List[Dict[str, Any]]):
        """
        Initialize with disease database.
        
        Args:
            disease_db: List of disease records from database
        """
        self.disease_db = disease_db
        self.min_confidence = 15

    def analyze_symptoms(
        self,
        symptoms: List[str],
        location: Optional[str] = None,
        severity: Optional[int] = None,
        duration: Optional[Dict] = None,
        history: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze symptoms and generate differential diagnosis.
        
        Returns:
            {
                "primary_diagnosis": "Disease Name",
                "confidence": 75,
                "alternative_diagnoses": [
                    {"disease": "Disease2", "confidence": 45},
                    {"disease": "Disease3", "confidence": 30},
                ],
                "risk_level": "medium",
                "reasoning": "Based on analysis...",
                "requires_emergency": False,
                "next_steps": ["List of recommended tests/actions"]
            }
        """
        
        # Step 1: Match symptoms to diseases
        disease_matches = self._match_symptoms_to_diseases(symptoms)

        # Step 2: Apply clinical filters
        if location:
            disease_matches = self._filter_by_location(disease_matches, location)

        if severity is not None:
            disease_matches = self._apply_severity_filter(disease_matches, severity)

        if duration:
            disease_matches = self._apply_duration_filter(disease_matches, duration)

        disease_matches = self._apply_symptom_combination_rules(disease_matches, symptoms)

        # Step 3: Rank by confidence
        ranked_diseases = self._rank_diseases(disease_matches)

        # Step 4: Generate reasoning
        contradictions = self.detect_contradictions(symptoms)
        if ranked_diseases:
            primary = ranked_diseases[0]
            alternatives = ranked_diseases[1:3]
            
            reasoning = self._generate_reasoning(
                primary, alternatives, symptoms, location, severity, duration
            )
            
            return {
                "primary_diagnosis": primary["disease"],
                "confidence": primary["confidence"],
                "alternative_diagnoses": [
                    {"disease": alt["disease"], "confidence": alt["confidence"]}
                    for alt in alternatives
                ],
                "risk_level": primary.get("risk_level", "medium"),
                "reasoning": reasoning,
                "requires_emergency": primary.get("emergency", False),
                "description": primary.get("description", ""),
                "symptoms_matched": primary.get("symptoms_matched", []),
                "next_steps": self._generate_next_steps(primary, alternatives),
                "contradictions": contradictions,
            }
        else:
            return {
                "primary_diagnosis": None,
                "confidence": 0,
                "alternative_diagnoses": [],
                "risk_level": "unknown",
                "reasoning": "Need more information to make a diagnosis.",
                "requires_emergency": False,
                "next_steps": ["Please describe your symptoms in more detail."],
                "contradictions": contradictions,
            }

    def _match_symptoms_to_diseases(self, symptoms: List[str]) -> List[Dict]:
        """Match user symptoms to diseases in database."""
        
        symptoms_lower = list(set(s.lower().strip() for s in symptoms))
        matches = []

        for disease in self.disease_db:
            disease_symptoms = [s.lower() for s in disease.get("symptoms", [])]
            
            # Count matching symptoms
            matched_count = 0
            for user_sym in symptoms_lower:
                for disease_sym in disease_symptoms:
                    # Direct match
                    if user_sym == disease_sym:
                        matched_count += 2
                    # Substring match — token-overlap to reduce false positives
                    else:
                        user_tokens = set(user_sym.split())
                        disease_tokens = set(disease_sym.split())
                        overlap = len(user_tokens & disease_tokens)
                        if overlap >= 2:
                            matched_count += 1

            if matched_count > 0:
                confidence = min(
                    100,
                    int(
                        (
                            matched_count /
                            max(1, len(symptoms_lower) * 2)
                        ) * 100
                    )
                )
                matches.append({
                    "disease": disease.get("disease_name"),
                    "confidence": confidence,
                    "risk_level": disease.get("risk_level", "medium"),
                    "emergency": disease.get("emergency", False),
                    "description": disease.get("description"),
                    "symptoms_matched": [
                        s for s in symptoms_lower
                        if s in disease_symptoms
                    ],
                    "full_record": disease,
                })

        return matches

    def _filter_by_location(self, matches: List[Dict], location: str) -> List[Dict]:
        """Boost confidence for diseases whose body_system or description matches location."""
        location_lower = location.lower()
        location_keywords = location_lower.split()

        for match in matches:
            description = match.get("description", "").lower()
            disease_name = match.get("disease", "").lower()
            body_system = match.get("full_record", {}).get("body_system", "").lower()

            matched = any(
                kw in description or kw in disease_name or kw in body_system
                for kw in location_keywords
                if len(kw) > 3
            )
            if matched:
                match["confidence"] = min(100, match["confidence"] + 10)

        return matches

    def _apply_severity_filter(self, matches: List[Dict], severity: int) -> List[Dict]:
        """Apply severity-based filtering."""
        # Boost confidence for diseases matching severity profile
        
        for match in matches:
            disease = match.get("full_record", {})
            risk_level = disease.get("risk_level", "medium")
            
            # High severity should correlate with certain risk levels
            if severity >= 8:
                if risk_level in ["high", "medium"]:
                    match["confidence"] = min(100, match["confidence"] + 15)
            elif severity >= 5:
                if risk_level in ["medium", "low"]:
                    match["confidence"] = min(100, match["confidence"] + 10)
            else:
                if risk_level == "low":
                    match["confidence"] = min(100, match["confidence"] + 5)

        return matches

    def _apply_duration_filter(self, matches: List[Dict], duration: Dict) -> List[Dict]:
        """Apply duration-based filtering."""
        # Different diseases have different typical durations
        
        value = duration.get("value", 0)
        unit = duration.get("unit", "days")

        # Convert to days for comparison
        days = value
        if unit == "hours":
            days = value / 24
        elif unit == "weeks":
            days = value * 7
        elif unit == "months":
            days = value * 30

        for match in matches:
            disease = match.get("full_record", {})
            # Acute diseases (fever, cold) typically short duration
            # Chronic diseases (psoriasis, diabetes) long duration
            if disease.get("body_system") in ["Respiratory", "Immune"]:
                if days <= 14:
                    match["confidence"] = min(100, match["confidence"] + 10)
            elif disease.get("body_system") in ["Dermatological", "Endocrine"]:
                if days > 30:
                    match["confidence"] = min(100, match["confidence"] + 5)

        return matches
    def _apply_symptom_combination_rules(
        self,
        matches: List[Dict],
        symptoms: List[str]
    ) -> List[Dict]:

        symptoms_lower = [s.lower() for s in symptoms]

        has_fever = "fever" in symptoms_lower
        has_cough = "cough" in symptoms_lower
        has_breathless = any(
            s in symptoms_lower
            for s in [
                "breathless",
                "shortness of breath",
                "difficulty breathing"
            ]
        )

        has_headache = "headache" in symptoms_lower
        has_body_pain = any(
            s in symptoms_lower
            for s in [
                "body pain",
                "muscle pain",
                "weakness"
            ]
        )

        has_chest_pain = "chest pain" in symptoms_lower
        has_sweating = "sweating" in symptoms_lower
        has_radiating = any(
            s in symptoms_lower
            for s in [
                "radiating",
                "left arm pain",
                "jaw pain"
            ]
        )

        has_confusion = "confusion" in symptoms_lower
        has_high_fever = any(
            x in symptoms_lower
            for x in [
                "high fever",
                "104 fever",
                "103 fever",
                "temperature 104",
                "temperature 103",
                "104f",
                "103f"
            ]
        )

        for match in matches:

            disease_name = match.get(
                "disease",
                ""
            ).lower()

            # Fever + cough + breathless
            if (
                has_fever
                and has_cough
                and has_breathless
            ):
                if any(
                    word in disease_name
                    for word in [
                        "pneumonia",
                        "bronchitis",
                        "respiratory infection"
                    ]
                ):
                    match["confidence"] = min(
                        100,
                        match["confidence"] + 25
                    )

            # Fever + headache + body pain
            if (
                has_fever
                and has_headache
                and has_body_pain
            ):
                if any(
                    word in disease_name
                    for word in [
                        "viral",
                        "influenza",
                        "flu",
                        "viral fever"
                    ]
                ):
                    match["confidence"] = min(
                        100,
                        match["confidence"] + 20
                    )

            # Chest pain + sweating + radiating
            if (
                has_chest_pain
                and has_sweating
                and has_radiating
            ):
                if any(
                    word in disease_name
                    for word in [
                        "heart attack",
                        "myocardial infarction",
                        "acute coronary syndrome"
                    ]
                ):
                    match["confidence"] = min(
                        100,
                        match["confidence"] + 40
                    )
                    match["emergency"] = True
                    match["risk_level"] = "high"

            # High fever + confusion → red flag
            if has_high_fever and has_confusion:
                match["emergency"] = True
                match["risk_level"] = "high"
                match["confidence"] = min(100, match["confidence"] + 35)

        return matches

    def detect_contradictions(self, symptoms: List[str]) -> List[str]:
        """Detect contradictory symptom pairs reported together."""
        s = {x.lower() for x in symptoms}
        contradictions = []
        if "fever" in s and "no fever" in s:
            contradictions.append("fever")
        if "cough" in s and "no cough" in s:
            contradictions.append("cough")
        return contradictions

    def _rank_diseases(self, matches: List[Dict]) -> List[Dict]:
        """Rank diseases by confidence score."""
        # Filter out very low confidence matches
        significant_matches = [m for m in matches if m["confidence"] >= self.min_confidence]

        for m in significant_matches:
            if m.get("emergency"):
                m["confidence"] = min(95, m["confidence"] + 10)

        # Sort by confidence descending
        ranked = sorted(significant_matches, key=lambda x: x["confidence"], reverse=True)

        return ranked[:5]  # Return top 5

    def _generate_reasoning(
        self,
        primary: Dict,
        alternatives: List[Dict],
        symptoms: List[str],
        location: Optional[str],
        severity: Optional[int],
        duration: Optional[Dict],
    ) -> str:
        """Generate clinical reasoning explanation."""
        
        reasoning = f"**Analysis Based On Your Information:**\n\n"
        
        # List what was learned
        reasoning += f"**Reported Symptoms:** {', '.join(symptoms)}\n"
        
        if location:
            reasoning += f"**Location:** {location}\n"
        
        if severity:
            reasoning += f"**Severity Level:** {severity}/10\n"
        
        if duration:
            reasoning += f"**Duration:** {duration.get('value')} {duration.get('unit')}\n"
        
        reasoning += f"\n**Clinical Assessment:**\n"
        reasoning += f"Your symptoms most strongly suggest **{primary['disease']}**, "
        reasoning += f"with a confidence score of {primary['confidence']}%.\n\n"
        
        if alternatives:
            reasoning += "**Other Possibilities to Consider:**\n"
            for i, alt in enumerate(alternatives, 1):
                reasoning += f"{i}. {alt['disease']} ({alt['confidence']}% match)\n"
        
        reasoning += f"\n**Risk Assessment:** {primary.get('risk_level', 'medium').title()}\n"
        
        return reasoning

    def _generate_next_steps(self, primary: Dict, alternatives: List[Dict]) -> List[str]:
        """Generate recommended next steps."""
        
        steps = []
        disease = primary.get("full_record", {})
        
        # Emergency check
        if primary.get("emergency"):
            steps.append("⚠️ **Seek immediate medical attention** if symptoms worsen")
        
        # Recommended tests
        tests = disease.get("recommended_tests", [])
        if tests:
            steps.extend([f"Get tested for: {t}" for t in tests[:3]])
        
        # Doctor type
        doctor = disease.get("doctor_type", "General Physician")
        steps.append(f"Consult a {doctor}")
        
        # Precautions
        precautions = disease.get("precautions", [])
        if precautions:
            steps.append(f"Follow precautions: {', '.join(precautions[:2])}")
        
        return steps

    def should_ask_more_questions(
        self,
        confidence: int,
        symptoms_collected: int,
    ) -> bool:
        """Determine if more questions are needed before diagnosis."""
        
        # If confidence is low, ask more questions
        if confidence < 40:
            return True
        
        # If we haven't collected enough information, ask more
        if symptoms_collected < 2:
            return True
        
        return False

    def validate_diagnosis_readiness(
        self,
        symptoms: List[str],
        location: Optional[str],
        severity: Optional[int],
        duration: Optional[Dict],
    ) -> Tuple[bool, str]:
        """
        Check if we have enough information for diagnosis.
        
        Returns:
            (is_ready, message)
        """
        
        if not symptoms:
            return False, "Please describe your main symptom first."
        
        if len(symptoms) < 2:
            return False, "I need a bit more information about your symptoms to provide an accurate assessment."
        
        if severity is None:
            return False, "Please rate the severity of your symptom."
        
        if duration is None:
            return False, "Please tell me how long you've had this symptom."
        
        # Check if we have enough info
        info_count = sum([
            bool(symptoms),
            bool(location),
            severity is not None,
            duration is not None,
        ])
        
        if info_count >= 3:
            return True, "I have enough information to provide an assessment."
        
        return False, "Please provide more details so I can give you a better assessment."
