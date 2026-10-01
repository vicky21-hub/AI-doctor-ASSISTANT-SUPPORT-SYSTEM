"""
ai_doctor_engine.py — Conversational AI engine with NLP symptom extraction.

Stage flow (matches frontend ConversationState exactly):
  greeting → asking_location → asking_severity → asking_duration → asking_history → diagnosis

Symptom detection uses two layers:
  1. Keyword map  — fast exact/substring match for common phrases
  2. extract_canonical_symptoms() — NLP normalization + body-part mapping
     catches: "knee pain", "severe knee pain while walking", etc.
"""

import re
import logging
from ai.human_health_engine import HumanHealthEngine
from ai.symptom_matcher import (
    extract_canonical_symptoms,
    correct_spelling,
    direct_disease_name_lookup,
    get_symptoms_from_disease_name,
)

logger = logging.getLogger(__name__)


class AIDoctorEngine:
    def __init__(self):
        self.human_engine = HumanHealthEngine()

        # ── Expanded keyword map ───────────────────────────────────────────────
        # Each key is the canonical symptom name stored in state["symptoms"].
        # Values are all phrases that should trigger detection of that symptom.
        self.symptoms_keywords = {
            # ── Fever / temperature ──────────────────────────────────────────
            "fever": [
                "fever", "high temperature", "high temp", "feeling hot",
                "temperature", "jvaram", "bukhar", "feverish", "chills",
                "body heat", "hot body",
            ],
            # ── Head ────────────────────────────────────────────────────────
            "headache": [
                "headache", "head ache", "migraine", "head pain", "head hurts",
                "tala noppi", "sir dard", "forehead pain", "temple pain",
                "pressure in head",
            ],
            # ── Respiratory ─────────────────────────────────────────────────
            "cough": [
                "cough", "coughing", "dry cough", "wet cough", "persistent cough",
                "khasi", "barking cough",
            ],
            "cold": [
                "cold", "runny nose", "blocked nose", "stuffy nose",
                "sneezing", "nasal congestion",
            ],
            "sore throat": [
                "sore throat", "throat pain", "throat ache", "throat hurts",
                "difficulty swallowing", "painful swallowing", "strep",
            ],
            "shortness of breath": [
                "shortness of breath", "breathless", "breathlessness",
                "cant breathe", "can't breathe", "difficulty breathing",
                "hard to breathe", "out of breath", "wheezing",
                "breathing difficulty", "breathing problem",
            ],
            # ── Chest ───────────────────────────────────────────────────────
            "chest pain": [
                "chest pain", "chest tightness", "chest pressure",
                "chest discomfort", "seena dard", "heart pain",
                "pain in chest", "tight chest",
            ],
            # ── Stomach / GI ────────────────────────────────────────────────
            "stomach pain": [
                "stomach pain", "stomach ache", "abdominal pain",
                "belly pain", "belly ache", "tummy pain", "tummy ache",
                "pet dard", "pet noppi", "gastric pain", "cramps",
                "abdominal cramps",
            ],
            "nausea": [
                "nausea", "nauseous", "vomiting", "vomit", "throwing up",
                "threw up", "puking", "sick to stomach", "ulti",
            ],
            "diarrhea": [
                "diarrhea", "diarrhoea", "loose motion", "loose stools",
                "watery stool", "frequent stools",
            ],
            "heartburn": [
                "heartburn", "acid reflux", "acidity", "burning stomach",
                "burning chest", "indigestion",
            ],
            # ── Joints / Musculoskeletal ─────────────────────────────────────
            "joint pain": [
                "joint pain", "joint ache", "joint swelling", "joint stiffness",
                "arthritis", "aching joints",
                # knee
                "knee pain", "knee ache", "knee aching", "knee hurts",
                "knee hurt", "knee swelling", "knee swollen", "knee stiff",
                "knee stiffness", "knee injury", "knee problem", "knee discomfort",
                "pain in knee", "pain in my knee", "my knee hurts",
                "severe knee pain", "knee pain while walking",
                "knee pain when walking", "knee pain while running",
                # hip
                "hip pain", "hip ache", "hip hurts",
                # ankle
                "ankle pain", "ankle ache", "ankle swelling", "ankle swollen",
                # elbow
                "elbow pain", "elbow ache", "elbow swelling",
                # wrist
                "wrist pain", "wrist ache", "wrist swelling",
                # toe
                "toe pain", "big toe pain", "toe swelling",
                # foot
                "foot pain", "foot ache", "heel pain",
                # general
                "gout", "uric acid",
            ],
            "back pain": [
                "back pain", "lower back pain", "upper back pain",
                "spine pain", "backache", "back ache", "kamar dard",
                "lumbar pain", "back hurts", "my back hurts",
            ],
            "muscle pain": [
                "muscle pain", "muscle ache", "body ache", "body pain",
                "soreness", "myalgia",
                # shoulder
                "shoulder pain", "shoulder ache", "shoulder hurts",
                # neck
                "neck pain", "neck ache", "neck stiff", "neck stiffness",
                # leg
                "leg pain", "leg ache", "leg cramp", "calf pain",
                # arm
                "arm pain", "arm ache",
            ],
            "stiffness": [
                "stiffness", "stiff", "rigid", "tight muscles",
                "morning stiffness", "stiff joints",
            ],
            # ── Mobility ────────────────────────────────────────────────────
            "difficulty walking": [
                "difficulty walking", "cant walk", "can't walk",
                "hard to walk", "limping", "limp", "walking pain",
                "pain while walking", "pain when walking",
                "trouble walking", "unable to walk",
            ],
            # ── Skin ────────────────────────────────────────────────────────
            "rash": [
                "rash", "skin rash", "itching", "itchy", "itchy skin",
                "red skin", "red spots", "hives", "bumps", "allergy",
                "skin allergy", "skin irritation",
            ],
            # ── Eyes ────────────────────────────────────────────────────────
            "eye pain": [
                "eye pain", "eye ache", "eye irritation", "red eyes",
                "itchy eyes", "watery eyes", "eye discharge",
            ],
            # ── Ears ────────────────────────────────────────────────────────
            "ear pain": [
                "ear pain", "ear ache", "earache", "ear infection",
                "ear discharge", "hearing loss",
            ],
            # ── Fatigue / Energy ─────────────────────────────────────────────
            "fatigue": [
                "tired", "tiredness", "fatigue", "weakness", "weak",
                "exhausted", "exhaustion", "no energy", "lethargic",
                "lethargy", "thakaan",
            ],
            # ── Dizziness ───────────────────────────────────────────────────
            "dizziness": [
                "dizziness", "dizzy", "vertigo", "lightheaded",
                "light headed", "spinning", "chakkar",
            ],
            # ── Urinary ─────────────────────────────────────────────────────
            "urinary symptoms": [
                "frequent urination", "burning urination", "painful urination",
                "blood in urine", "cloudy urine", "urinary pain",
            ],
            # ── Mental health ────────────────────────────────────────────────
            "anxiety": [
                "anxiety", "anxious", "nervousness", "nervous", "panic",
                "panic attack", "stress", "worried", "worry",
            ],
            "depression": [
                "depression", "depressed", "sadness", "sad", "low mood",
                "hopeless", "no motivation", "feeling down",
            ],
            "insomnia": [
                "insomnia", "can't sleep", "cannot sleep", "sleep problems",
                "trouble sleeping", "sleepless", "waking up at night",
            ],
            # ── Swelling (general) ───────────────────────────────────────────
            "swelling": [
                "swelling", "swollen", "swells", "puffiness", "puffy",
                "inflammation", "inflamed",
            ],
            # ── Weight / appetite ────────────────────────────────────────────
            "weight loss": [
                "weight loss", "losing weight", "lost weight",
                "loss of appetite", "no appetite", "not eating",
            ],
        }

    # ── Language detection ─────────────────────────────────────────────────────

    def detect_language(self, text: str) -> str:
        text_lower = text.lower()
        telugu_words = ["nenu", "meeru", "em", "ela", "undi", "ledu", "baga",
                        "chala", "noppi", "jvaram", "undhi", "tala"]
        if any(w in text_lower for w in telugu_words):
            return "te"
        hindi_words = ["mai", "aap", "kya", "hai", "nahi", "bahut", "thoda",
                       "kar", "dard", "bukhar", "seena", "khasi"]
        if any(w in text_lower for w in hindi_words):
            return "hi"
        return "en"

    # ── Symptom detection ──────────────────────────────────────────────────────

    def detect_symptoms(self, text: str) -> list:
        """
        Three-layer symptom detection. Never returns empty if any medical
        term (even misspelled) is found.

        Layer 1 — spell-correct the input first, then run keyword map
        Layer 2 — NLP extract_canonical_symptoms (handles body-part phrases)
        Layer 3 — direct disease-name fuzzy lookup (catches "psoasis",
                  "diabtes", "migrene" typed as standalone disease names)
        """
        # Apply spell correction before any matching
        corrected = correct_spelling(text)
        corrected_lower = corrected.lower()
        original_lower  = text.lower()

        detected = []

        # Layer 1: keyword map on both original and corrected text
        for symptom, keywords in self.symptoms_keywords.items():
            if any(kw in corrected_lower or kw in original_lower for kw in keywords):
                if symptom not in detected:
                    detected.append(symptom)

        # Layer 2: NLP canonical extraction (on corrected text)
        nlp_symptoms = extract_canonical_symptoms(corrected)
        for s in nlp_symptoms:
            # filter out the internal __disease_match__ tag — handled separately
            if not s.startswith("__disease_match__") and s not in detected:
                detected.append(s)

        # Layer 3: direct disease-name fuzzy lookup
        # Fires when layers 1+2 found nothing (e.g. user typed just "psoasis")
        disease_match_tag = None
        if not detected:
            # Check if layer 2 left a disease-match tag
            for s in nlp_symptoms:
                if s.startswith("__disease_match__:"):
                    disease_match_tag = s  # format: __disease_match__:Name:score
                    break

            if not disease_match_tag:
                # Run direct lookup independently
                matched_name, score = direct_disease_name_lookup(text, threshold=70)
                if matched_name and score >= 70:
                    disease_match_tag = f"__disease_match__:{matched_name}:{score}"

            if disease_match_tag:
                _, dname, dscore = disease_match_tag.split(":", 2)
                resolved = get_symptoms_from_disease_name(dname)
                for s in resolved:
                    if s not in detected:
                        detected.append(s)
                logger.info(
                    "[AIDoctorEngine] disease-name match: %r → %s (score=%s)",
                    text, dname, dscore,
                )
                print(f"[DEBUG] Disease-name match: '{text}' → {dname} (score={dscore})")

        if detected:
            logger.info("[AIDoctorEngine] detected symptoms: %s", detected)
            print(f"[DEBUG] Extracted symptoms from '{text}': {detected}")
        else:
            print(f"[DEBUG] No symptoms detected from: '{text}'")

        return detected, disease_match_tag

    def _parse_disease_match_tag(self, tag: str) -> tuple:
        """Parse '__disease_match__:Name:score' → (name, int_score)."""
        if not tag or not tag.startswith("__disease_match__:"):
            return None, 0
        parts = tag.split(":", 2)
        if len(parts) == 3:
            try:
                return parts[1], int(float(parts[2]))
            except ValueError:
                return parts[1], 75
        return None, 0

    # ── Conversation state machine ─────────────────────────────────────────────

    def get_conversation_state(self, message: str, current_state: dict) -> dict:
        """Advance conversation state — stage names match frontend exactly."""
        state = dict(current_state) if current_state else {}
        stage = state.get("stage", "greeting")

        if stage == "greeting":
            detected, disease_tag = self.detect_symptoms(message)
            if detected:
                state["symptoms"] = detected
                state["stage"] = "asking_location"
                # Store disease-name match metadata for confirmation message
                if disease_tag:
                    dname, dscore = self._parse_disease_match_tag(disease_tag)
                    state["disease_name_match"] = dname
                    state["disease_name_score"] = dscore
            # If still nothing, leave stage as greeting so we re-ask
            return state

        # Confirmation stage: user responding to "Did you mean X?"
        if stage == "confirming_disease":
            msg_lower = message.lower().strip()
            if any(w in msg_lower for w in ["yes", "yeah", "correct", "right", "yep", "ya", "haan", "avunu"]):
                # Confirmed — advance with stored symptoms
                state["stage"] = "asking_location"
            else:
                # Rejected — ask them to rephrase
                state["stage"] = "greeting"
                state["symptoms"] = []
                state["disease_name_match"] = None
            return state

        if stage == "asking_location":
            state["location"] = message
            state["stage"] = "asking_severity"
            return state

        if stage == "asking_severity":
            severity_map = {
                "mild":     ["mild", "slight", "little", "not bad", "1", "2", "3"],
                "moderate": ["moderate", "medium", "average", "somewhat", "4", "5", "6"],
                "severe":   ["severe", "bad", "worst", "intense", "unbearable",
                             "very bad", "7", "8", "9", "10"],
            }
            msg_lower = message.lower()
            for level, keywords in severity_map.items():
                if any(k in msg_lower for k in keywords):
                    state["severity"] = level
                    break
            else:
                state["severity"] = "moderate"
            state["stage"] = "asking_duration"
            return state

        if stage == "asking_duration":
            duration_patterns = [
                (r"(\d+)\s*days?",   "days"),
                (r"(\d+)\s*weeks?",  "weeks"),
                (r"(\d+)\s*hours?",  "hours"),
                (r"(\d+)\s*months?", "months"),
            ]
            for pattern, unit in duration_patterns:
                m = re.search(pattern, message.lower())
                if m:
                    state["duration"] = f"{m.group(1)} {unit}"
                    break
            else:
                state["duration"] = "recent"
            state["stage"] = "asking_history"
            return state

        if stage == "asking_history":
            state["history"] = message
            state["stage"] = "diagnosis"
            return state

        return state

    # ── Response formatting ────────────────────────────────────────────────────

    def format_response(self, assessment: dict) -> str:
        lines = [
            f"✅ **Possible condition:** {assessment.get('disease', 'Unknown')}",
            f"**Confidence:** {assessment.get('confidence', 0)}%",
            f"**Risk level:** {assessment.get('risk_level', 'low').upper()}",
            f"**Description:** {assessment.get('description', '')}",
        ]
        if assessment.get("symptoms"):
            lines.append(f"**Key symptoms:** {', '.join(assessment['symptoms'][:5])}")
        if assessment.get("causes"):
            lines.append(f"**Likely causes:** {', '.join(assessment['causes'][:4])}")
        if assessment.get("medicines"):
            lines.append("**OTC medicine suggestions:**")
            lines.extend([f"• {m}" for m in assessment["medicines"]])
        if assessment.get("precautions"):
            lines.append("**Precautions:**")
            lines.extend([f"• {p}" for p in assessment["precautions"]])
        if assessment.get("diet"):
            lines.append("**Recommended diet:**")
            lines.extend([f"• {d}" for d in assessment["diet"]])
        if assessment.get("home_remedies"):
            lines.append("**Home remedies:**")
            lines.extend([f"• {r}" for r in assessment["home_remedies"][:3]])
        if assessment.get("recommended_tests"):
            lines.append("**Recommended tests:**")
            lines.extend([f"• {t}" for t in assessment["recommended_tests"]])
        if assessment.get("emergency") and assessment.get("emergency_warnings"):
            lines.append("⚠️ **Emergency warning:**")
            for w in assessment["emergency_warnings"]:
                lines.append(f"• {w.get('warning', '')}")
        lines.append(f"**Consult:** {assessment.get('doctor_type', 'General Physician')}")
        lines.append("---")
        lines.append("⚠️ *This is not a medical diagnosis. Always consult a licensed doctor.*")
        return "\n\n".join(lines)

    def get_language_response(self, response_type: str, language: str) -> str:
        responses = {
            "no_symptoms": {
                "en": (
                    "I couldn't identify specific symptoms from your message.\n\n"
                    "Please try describing like:\n"
                    "• \"I have knee pain while walking\"\n"
                    "• \"I have fever and headache\"\n"
                    "• \"My chest feels tight\"\n"
                    "• \"I have joint swelling and pain\""
                ),
                "te": "నేను నిర్దిష్ట లక్షణాలను గుర్తించలేకపోయాను. దయచేసి మీరు అనుభవిస్తున్నదాన్ని వివరించండి (ఉదా: మోకాలు నొప్పి, జ్వరం, దగ్గు).",
                "hi": "मैं विशिष्ट लक्षणों की पहचान नहीं कर सका। कृपया बताएं (जैसे: घुटने में दर्द, बुखार, खांसी)।",
            },
            "emergency": {
                "en": "⚠️ EMERGENCY DETECTED! Please seek immediate medical attention. Call emergency services (108) or go to the nearest hospital right away!",
                "te": "⚠️ అత్యవసర పరిస్థితి! వెంటనే వైద్య సహాయం పొందండి. 108 కాల్ చేయండి!",
                "hi": "⚠️ आपातकालीन स्थिति! तत्काल चिकित्सा सहायता लें। 108 को कॉल करें!",
            },
            "ask_location": {
                "en": "I understand. Where exactly do you feel this? (e.g., left knee, right side, center of chest)",
                "te": "అర్థమైంది. ఇది ఎక్కడ అనిపిస్తోంది? (ఉదా: ఎడమ మోకాలు, ఛాతీ మధ్య)",
                "hi": "समझ गया। यह कहाँ महसूस हो रहा है? (जैसे: बाएं घुटने, छाती के बीच)",
            },
            "ask_severity": {
                "en": "On a scale of 1–10, how severe is it? (1 = mild, 10 = unbearable)",
                "te": "1 నుండి 10 వరకు, నొప్పి ఎంత తీవ్రంగా ఉంది?",
                "hi": "1 से 10 के पैमाने पर, यह कितना गंभीर है?",
            },
            "ask_duration": {
                "en": "How long have you been experiencing this? (e.g., 2 hours, 3 days, a week)",
                "te": "ఇది ఎంత కాలం నుండి ఉంది? (ఉదా: 2 గంటలు, 3 రోజులు)",
                "hi": "यह कितने समय से हो रहा है? (जैसे: 2 घंटे, 3 दिन)",
            },
            "ask_history": {
                "en": "Almost done! Did you have any recent injury, heavy activity, or unusual food?",
                "te": "దగ్గరగా వచ్చాం! ఇటీవల గాయం, భారమైన పని లేదా వేరే తిన్నారా?",
                "hi": "लगभग हो गया! क्या हाल ही में चोट, भारी काम या कुछ अलग खाया?",
            },
        }
        return responses.get(response_type, {}).get(language, responses[response_type]["en"])

    # ── Main response generator ────────────────────────────────────────────────

    def generate_response(self, symptoms: list, state: dict, language: str = "en") -> dict:
        stage = state.get("stage", "greeting")

        # ── Disease-name confirmation stage ───────────────────────────────────
        if stage == "confirming_disease":
            dname = state.get("disease_name_match", "")
            dscore = state.get("disease_name_score", 75)
            confirm_msgs = {
                "en": (
                    f'Did you mean **{dname}**?\n\n'
                    f'I found a close match (confidence: {dscore}%) for what you typed.\n\n'
                    f'Reply **Yes** to continue the consultation for {dname}, '
                    f'or describe your symptoms differently.'
                ),
                "te": (
                    f'మీరు **{dname}** గురించి చెప్తున్నారా?\n\n'
                    f'దయచేసి **అవును** అని చెప్పండి లేదా మీ లక్షణాలు వేరేగా వివరించండి.'
                ),
                "hi": (
                    f'क्या आपका मतलब **{dname}** था?\n\n'
                    f'कृपया **हाँ** कहें या अपने लक्षण अलग तरह से बताएं।'
                ),
            }
            return {
                "reply": confirm_msgs.get(language, confirm_msgs["en"]),
                "state": state,
                "emergency": False,
                "is_diagnosis": False,
            }

        # ── No symptoms found ─────────────────────────────────────────────────
        if not symptoms:
            return {
                "reply": self.get_language_response("no_symptoms", language),
                "state": state,
                "emergency": False,
                "is_diagnosis": False,
            }

        # ── Consultation stages ───────────────────────────────────────────────
        if stage == "asking_location":
            return {"reply": self.get_language_response("ask_location", language), "state": state, "emergency": False, "is_diagnosis": False}
        if stage == "asking_severity":
            return {"reply": self.get_language_response("ask_severity", language), "state": state, "emergency": False, "is_diagnosis": False}
        if stage == "asking_duration":
            return {"reply": self.get_language_response("ask_duration", language), "state": state, "emergency": False, "is_diagnosis": False}
        if stage == "asking_history":
            return {"reply": self.get_language_response("ask_history", language),  "state": state, "emergency": False, "is_diagnosis": False}

        # ── Final diagnosis ───────────────────────────────────────────────────
        assessment = self.human_engine.assess(
            text=" ".join(symptoms),
            symptoms=symptoms,
            severity=state.get("severity", ""),
            history=state.get("duration", ""),
        )

        if assessment.get("emergency"):
            return {
                "reply": self.get_language_response("emergency", language),
                "state": {**state, "stage": "diagnosis"},
                "emergency": True,
                "is_diagnosis": True,
            }

        return {
            "reply": self.format_response(assessment),
            "state": {
                **state,
                "stage": "diagnosis",
                "diagnosis": assessment.get("disease"),
                "risk": assessment.get("risk_level"),
            },
            "emergency": False,
            "is_diagnosis": True,
        }

    # ── Entry point ───────────────────────────────────────────────────────────

    def process_message(self, message: str, state: dict = None) -> dict:
        if not state:
            state = {}
        language = self.detect_language(message)
        prev_stage = state.get("stage", "greeting")
        state = self.get_conversation_state(message, state)

        # If greeting produced a disease-name match but no prior confirmation
        # was shown yet, switch to confirming_disease stage
        if (
            prev_stage == "greeting"
            and state.get("stage") == "asking_location"
            and state.get("disease_name_match")
        ):
            state["stage"] = "confirming_disease"

        return self.generate_response(state.get("symptoms", []), state, language)
