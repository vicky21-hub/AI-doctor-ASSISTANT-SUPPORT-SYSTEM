"""
emergency_detector.py — Medical emergency detection with fuzzy matching.

Detects critical conditions requiring immediate attention:
  - Cardiac (heart attack, cardiac arrest)
  - Neurological (stroke, seizure)
  - Respiratory (severe breathing failure)
  - Anaphylaxis (severe allergic reaction)
  - Abdominal emergency
  - Severe bleeding
  - Diabetic emergency
  - Meningitis signs
"""

import re
from typing import Any, Dict, List

from services.knowledge_service import EMERGENCY_RULES

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


# ── Extended emergency patterns ────────────────────────────────────────────────
EXTENDED_EMERGENCIES = [
    {
        "condition": "Possible Heart Attack",
        "keywords": [
            "crushing chest pain", "chest pain radiating", "radiating to arm",
            "radiating to jaw", "left arm pain", "jaw pain with chest",
            "squeezing chest", "elephant on chest", "heart attack",
            "sudden chest pain", "sweating with chest pain",
        ],
        "warning": "⚠️ CARDIAC EMERGENCY: These symptoms may indicate a heart attack. Call 108/112 immediately and chew one aspirin if not allergic.",
        "doctor_type": "Cardiologist",
        "severity": "critical",
    },
    {
        "condition": "Stroke Warning (FAST)",
        "keywords": [
            "face drooping", "arm weakness", "speech difficulty", "sudden confusion",
            "one sided weakness", "one-sided numbness", "sudden vision loss",
            "sudden severe headache", "can't speak", "slurred speech",
            "stroke", "brain attack",
        ],
        "warning": "⚠️ STROKE EMERGENCY (F.A.S.T): Face drooping, Arm weakness, Speech difficulty = Time to call 108 NOW. Every minute matters.",
        "doctor_type": "Neurologist",
        "severity": "critical",
    },
    {
        "condition": "Severe Respiratory Distress",
        "keywords": [
            "can't breathe", "cannot breathe", "no breath", "blue lips",
            "blue fingernails", "gasping", "choking", "stridor",
            "severe wheezing", "breathing stopped", "respiratory failure",
        ],
        "warning": "⚠️ BREATHING EMERGENCY: Inability to breathe is life-threatening. Call 108 immediately.",
        "doctor_type": "Pulmonologist / Emergency",
        "severity": "critical",
    },
    {
        "condition": "Anaphylaxis (Severe Allergic Reaction)",
        "keywords": [
            "throat swelling", "swelling throat", "tongue swelling",
            "anaphylaxis", "anaphylactic", "face swelling severe",
            "throat closing", "lips swelling", "can't swallow suddenly",
        ],
        "warning": "⚠️ ANAPHYLAXIS: Severe allergic reaction can block airway. Call 108 and use epinephrine (EpiPen) if available.",
        "doctor_type": "Emergency / Allergist",
        "severity": "critical",
    },
    {
        "condition": "Seizure / Convulsions",
        "keywords": [
            "seizure", "convulsions", "convulsion", "shaking uncontrollably",
            "epilepsy attack", "fits", "uncontrolled shaking",
            "loss of consciousness", "tonic clonic", "epileptic",
        ],
        "warning": "⚠️ SEIZURE: Place person on their side, clear the area, do NOT put anything in mouth. Call 108.",
        "doctor_type": "Neurologist",
        "severity": "critical",
    },
    {
        "condition": "Severe Abdominal Emergency",
        "keywords": [
            "vomiting blood", "blood in vomit", "black stool",
            "rigid abdomen", "board-like abdomen", "severe abdominal pain sudden",
            "abdomen hard as board", "appendicitis", "perforated ulcer",
        ],
        "warning": "⚠️ ABDOMINAL EMERGENCY: These signs suggest internal bleeding or perforation. Go to the emergency room immediately.",
        "doctor_type": "Emergency Surgeon",
        "severity": "critical",
    },
    {
        "condition": "Uncontrolled Bleeding",
        "keywords": [
            "bleeding won't stop", "uncontrolled bleeding", "severe bleeding",
            "blood won't stop", "deep wound bleeding", "arterial bleeding",
            "gushing blood",
        ],
        "warning": "⚠️ BLEEDING EMERGENCY: Apply firm pressure to the wound. Call 108 immediately.",
        "doctor_type": "Emergency / Surgeon",
        "severity": "critical",
    },
    {
        "condition": "Diabetic Emergency (Hypoglycemia / DKA)",
        "keywords": [
            "diabetic emergency", "blood sugar very low", "hypoglycemia severe",
            "unconscious diabetic", "diabetic coma", "dka",
            "diabetic ketoacidosis", "shaking diabetic", "sugar crash",
        ],
        "warning": "⚠️ DIABETIC EMERGENCY: If conscious give sugar immediately. If unconscious call 108.",
        "doctor_type": "Endocrinologist / Emergency",
        "severity": "critical",
    },
    {
        "condition": "Meningitis Signs",
        "keywords": [
            "stiff neck with fever", "neck stiffness fever", "photophobia fever",
            "sensitivity to light fever", "meningitis", "meningeal",
            "purple rash fever", "non-blanching rash",
        ],
        "warning": "⚠️ POSSIBLE MENINGITIS: Fever + stiff neck + sensitivity to light = medical emergency. Call 108 now.",
        "doctor_type": "Neurologist / Emergency",
        "severity": "critical",
    },
    {
        "condition": "High Fever in Child (> 104°F)",
        "keywords": [
            "fever above 104", "fever 105", "fever 106", "very high fever child",
            "child seizure fever", "febrile seizure",
        ],
        "warning": "⚠️ PEDIATRIC EMERGENCY: Dangerously high fever in a child. Seek emergency care immediately.",
        "doctor_type": "Pediatrician / Emergency",
        "severity": "critical",
    },
    {
        "condition": "Unconsciousness / Unresponsiveness",
        "keywords": [
            "unconscious", "unresponsive", "passed out", "fainted", "not waking up",
            "collapsed", "person not responding",
        ],
        "warning": "⚠️ UNCONSCIOUS PATIENT: Check breathing, place in recovery position. Call 108 immediately.",
        "doctor_type": "Emergency",
        "severity": "critical",
    },
    {
        "condition": "Suspected Poisoning / Overdose",
        "keywords": [
            "swallowed poison", "ingested chemicals", "drug overdose",
            "medicine overdose", "poisoning", "rat poison", "bleach swallowed",
        ],
        "warning": "⚠️ POISONING: Do NOT induce vomiting. Call Poison Control or 108 immediately.",
        "doctor_type": "Emergency / Toxicology",
        "severity": "critical",
    },
]

# Fuzzy-match threshold for partial emergency keyword detection
FUZZY_THRESHOLD = 78


class EmergencyDetector:
    def __init__(self):
        self.rules: List[Dict[str, Any]] = EMERGENCY_RULES
        self.extended_rules = EXTENDED_EMERGENCIES

    def _fuzzy_keyword_match(self, text: str, keyword: str) -> bool:
        """Check if keyword approximately appears in text using fuzzy matching."""
        if not RAPIDFUZZ_AVAILABLE:
            return keyword in text
        # Sliding window over text tokens
        words = text.split()
        kw_words = keyword.split()
        window_size = len(kw_words)
        for i in range(max(1, len(words) - window_size + 1)):
            window = " ".join(words[i: i + window_size])
            if fuzz.ratio(window, keyword) >= FUZZY_THRESHOLD:
                return True
        return False

    def _check_rule(self, text_lower: str, symptoms: List[str], keywords: List[str]) -> bool:
        sym_text = " ".join(symptoms).lower()
        combined = text_lower + " " + sym_text
        for keyword in keywords:
            kl = keyword.lower()
            # Exact match
            if kl in combined:
                return True
            # Fuzzy match
            if self._fuzzy_keyword_match(combined, kl):
                return True
        return False

    def detect(self, text: str, symptoms: List[str] = None) -> Dict[str, Any]:
        text_lower = text.lower()
        symptoms = symptoms or []
        matches = []
        seen_conditions = set()

        # Check knowledge-base rules
        for rule in self.rules:
            rule_keywords = [k.lower() for k in rule.get("keywords", [])]
            if self._check_rule(text_lower, symptoms, rule_keywords):
                condition = rule.get("condition", "Emergency")
                if condition not in seen_conditions:
                    seen_conditions.add(condition)
                    matches.append({
                        "condition": condition,
                        "warning": rule.get("warning", "Seek immediate medical attention."),
                        "doctor_type": rule.get("doctor_type", "Emergency"),
                        "severity": "critical",
                    })

        # Check extended rules
        for rule in self.extended_rules:
            condition = rule["condition"]
            if condition in seen_conditions:
                continue
            if self._check_rule(text_lower, symptoms, rule["keywords"]):
                seen_conditions.add(condition)
                matches.append({
                    "condition": condition,
                    "warning": rule["warning"],
                    "doctor_type": rule["doctor_type"],
                    "severity": rule.get("severity", "critical"),
                })

        is_emergency = len(matches) > 0

        return {
            "emergency": is_emergency,
            "warnings": matches,
            "emergency_level": "critical" if is_emergency else "none",
            "call_number": "108" if is_emergency else None,
        }

    def is_red_flag_symptom(self, symptom: str) -> bool:
        """Quick check if a symptom string alone is a red flag."""
        red_flags = [
            "chest pain", "difficulty breathing", "can't breathe", "stroke",
            "seizure", "unconscious", "vomiting blood", "severe bleeding",
            "loss of consciousness", "severe chest pain",
        ]
        sl = symptom.lower()
        return any(rf in sl for rf in red_flags)
