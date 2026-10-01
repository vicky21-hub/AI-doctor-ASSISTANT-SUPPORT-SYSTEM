"""
risk_calculator.py — Multi-factor medical risk assessment.

Factors:
  1. Disease baseline risk (from knowledge base)
  2. Symptom severity reported by patient
  3. Emergency flag from EmergencyDetector
  4. Duration of symptoms
  5. Number and type of symptoms
  6. Presence of red-flag symptoms
"""

from typing import Dict, List


# Symptoms that automatically elevate risk
HIGH_RISK_SYMPTOMS = {
    "chest pain", "shortness of breath", "difficulty breathing", "severe headache",
    "loss of consciousness", "blood in stool", "vomiting blood", "blood in urine",
    "sudden vision loss", "one-sided weakness", "face drooping", "seizure",
    "severe abdominal pain", "high fever", "stiff neck",
}

MEDIUM_RISK_SYMPTOMS = {
    "fever", "dizziness", "persistent cough", "nausea", "vomiting",
    "back pain", "joint pain", "fatigue", "swelling", "rash",
    "ear pain", "sore throat", "headache",
}


class RiskCalculator:
    def classify_severity(self, severity_text: str) -> str:
        if not severity_text:
            return "medium"
        text = severity_text.lower()
        # Numeric severity
        try:
            nums = [int(x) for x in text.split() if x.isdigit()]
            if nums:
                n = nums[0]
                if n >= 7:
                    return "high"
                if n >= 4:
                    return "medium"
                return "low"
        except Exception:
            pass

        if any(w in text for w in ["severe", "very bad", "unbearable", "intense", "10", "9", "8", "worst"]):
            return "high"
        if any(w in text for w in ["moderate", "average", "somewhat", "fair", "5", "6", "7"]):
            return "medium"
        return "low"

    def classify_duration(self, duration_text: str) -> str:
        """Longer duration → higher chronic risk."""
        if not duration_text:
            return "acute"
        text = duration_text.lower()
        if any(w in text for w in ["month", "week", "chronic", "long", "years"]):
            return "chronic"
        if any(w in text for w in ["day", "days", "2 days", "3 days"]):
            return "subacute"
        return "acute"

    def check_red_flag_symptoms(self, symptoms: List[str]) -> bool:
        symptom_set = {s.lower() for s in symptoms}
        return bool(symptom_set & HIGH_RISK_SYMPTOMS)

    def calculate(
        self,
        disease_risk: str,
        severity_text: str,
        emergency_flag: bool,
        duration: str = "",
        symptoms: List[str] = None,
    ) -> Dict[str, str]:
        symptoms = symptoms or []

        # Emergency overrides everything
        if emergency_flag:
            return {
                "risk_level": "high",
                "reason": "Emergency symptom detected. Immediate medical attention required.",
                "color": "red",
                "action": "Go to emergency room or call 108 immediately.",
            }

        severity  = self.classify_severity(severity_text)
        duration_class = self.classify_duration(duration)
        has_red_flag = self.check_red_flag_symptoms(symptoms)

        # Score system
        score = 0
        if disease_risk == "high":   score += 3
        if disease_risk == "medium": score += 2
        if disease_risk == "low":    score += 1

        if severity == "high":       score += 3
        if severity == "medium":     score += 2
        if severity == "low":        score += 1

        if duration_class == "chronic":  score += 2
        if duration_class == "subacute": score += 1

        if has_red_flag:             score += 3

        # Count medium/high risk symptoms
        sym_lower = {s.lower() for s in symptoms}
        medium_count = len(sym_lower & MEDIUM_RISK_SYMPTOMS)
        if medium_count >= 3: score += 1
        if medium_count >= 5: score += 1

        # Classify
        if score >= 7 or has_red_flag:
            return {
                "risk_level": "high",
                "reason": (
                    "High-risk profile: " +
                    ("red-flag symptoms present. " if has_red_flag else "") +
                    (f"Severity: {severity}. " if severity else "") +
                    (f"Duration: {duration_class} presentation." if duration else "")
                ),
                "color": "red",
                "action": "Consult a doctor today or go to emergency if symptoms worsen.",
            }

        if score >= 4:
            return {
                "risk_level": "medium",
                "reason": (
                    f"Moderate risk. Severity: {severity}. "
                    f"Duration: {duration_class} presentation. Monitor closely."
                ),
                "color": "orange",
                "action": "Visit a doctor within 24-48 hours if symptoms do not improve.",
            }

        return {
            "risk_level": "low",
            "reason": f"Low-risk presentation. Severity: {severity}. Symptoms appear manageable at home.",
            "color": "green",
            "action": "Home management appropriate. See a doctor if symptoms persist more than 3 days.",
        }
