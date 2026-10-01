"""
enhanced_ai_doctor_engine.py — Intelligent doctor-style consultation engine.

Core principle:
  Every message is fully parsed for ALL medical information before asking anything.
  The engine never asks for information already provided.
  Questions are chosen based on what is most clinically important and still unknown.

Consultation rules applied:
  1.  Extract all info from every message before deciding the next question.
  2.  Never ask a question whose answer is already in the patient record.
  3.  Capture side-symptoms mentioned mid-consultation.
  4.  Expanded emergency detection — chest tightness = cardiac.
  5.  Emergency override stops consultation immediately.
  6.  Diagnosis safety guards (Viral Fever / Dengue / Migraine / Malaria).
  7.  Evidence-based confidence (High ≥70 / Medium 40-69 / Low <40).
  8.  Doctor-like natural language throughout.
  9.  Patient safety > questionnaire completion.
  10. Summary must list all collected fields.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple

from utils.text_normalizer import TextNormalizer, YES_VARIANTS, NO_VARIANTS
from utils.disease_question_trees import (
    classify_symptom_category,
    get_next_unanswered_question,
    build_symptom_context,
    QUESTION_STAGES,
    get_question_tree,
)
from utils.medical_reasoning_engine import MedicalReasoningEngine
from services.knowledge_service import get_diseases, find_disease

logger = logging.getLogger(__name__)

MAX_INVALID_ATTEMPTS = 3

# ---------------------------------------------------------------------------
# Emergency keywords  (chest tightness treated as cardiac)
# ---------------------------------------------------------------------------
EMERGENCY_KEYWORDS = [
    "chest pain radiating", "crushing chest", "crushing pain",
    "left arm pain", "pain in left arm", "jaw pain",
    "chest tightness", "tight chest", "tightness in chest",
    "pressure in chest", "chest pressure", "squeezing chest",
    "heart attack",
    "can't breathe", "cannot breathe", "unable to breathe",
    "severe breathing difficulty", "struggling to breathe",
    "blue lips", "unconscious", "not waking up",
    "loss of consciousness", "lost consciousness",
    "seizure", "stroke", "facial droop", "slurred speech",
    "sudden numbness", "sudden weakness one side",
    "vomiting blood", "blood in vomit",
    "severe bleeding", "uncontrolled bleeding", "coughing blood",
]

EMERGENCY_COMBOS = [
    (["chest pain", "shortness of breath"], "chest pain with shortness of breath"),
    (["chest pain", "breathless"],           "chest pain with breathlessness"),
    (["chest pain", "sweating"],             "chest pain with sweating"),
    (["chest pain", "arm pain"],             "chest pain radiating to arm"),
    (["chest pain", "jaw"],                  "chest pain radiating to jaw"),
    (["chest tightness", "breathless"],      "chest tightness with difficulty breathing"),
    (["tight chest", "breath"],              "chest tightness with breathing difficulty"),
]

CATEGORY_DISPLAY = {
    "vomiting":          "Gastrointestinal / Vomiting",
    "fever":             "Fever / Infection",
    "chest_pain":        "Chest Pain / Cardiac",
    "joint_pain":        "Joint / Musculoskeletal",
    "skin":              "Skin Condition",
    "back_pain":         "Back Pain",
    "headache":          "Headache / Migraine",
    "respiratory":       "Respiratory",
    "stomach_pain":      "Stomach / GI",
    "urinary":           "Urinary Symptoms",
    "mental_health":     "Mental Health",
    "dizziness":         "Dizziness / Vertigo",
    "fatigue":           "Fatigue / Weakness",
    "eye":               "Eye Symptoms",
    "ear":               "Ear Symptoms",
    "diabetes_symptoms": "Diabetes-related Symptoms",
    "default":           "General Symptoms",
}

QUESTION_EXAMPLES = {
    "temperature":    ["101 F", "38.5 C", "Not checked"],
    "duration":       ["2 hours", "since this morning", "3 days", "1 week"],
    "severity":       ["7", "5", "mild", "moderate", "severe"],
    "itching_sev":    ["6", "8", "mild", "moderate", "severe"],
    "vomit_count":    ["3 times", "once", "continuously"],
    "which_joints":   ["knee", "both knees", "hip and ankle", "wrist"],
    "affected_areas": ["elbows", "scalp and knees", "full body"],
    "location":       ["upper abdomen", "lower back", "left side of chest", "forehead"],
    "character":      ["throbbing", "dull pressure", "sharp pain", "burning", "tight"],
    "cough_type":     ["dry cough", "wet cough with mucus"],
    "mucus_color":    ["clear", "yellow", "green", "no mucus"],
    "main_symptom":   ["anxiety", "low mood", "can't sleep"],
    "sleep_quality":  ["can't fall asleep", "wake up many times"],
    "sleep_hours":    ["6 hours", "8 hours", "only 4 hours"],
    "type":           ["room is spinning", "lightheaded", "unsteady"],
    "both_eyes":      ["left eye", "right eye", "both eyes"],
    "both_ears":      ["left ear", "right ear", "both ears"],
    "frequency":      ["8 times a day", "every 2 hours"],
    "diet":           ["vegetarian", "irregular meals", "balanced diet"],
    "triggers":       ["stress", "certain foods", "pollen", "unknown"],
    "description":    ["sharp pain", "constant dull ache", "burning feeling"],
}

RESTART_WORDS     = {"1", "continue", "keep going", "same"}
NEW_CONSULT_WORDS = {"2", "new", "restart", "start new", "new consultation", "start over"}

BODY_WORDS = {
    "head", "forehead", "temple", "back", "neck", "chest", "abdomen",
    "stomach", "belly", "arm", "leg", "knee", "hip", "shoulder", "ankle",
    "wrist", "elbow", "toe", "foot", "eye", "ear", "upper", "lower",
    "left", "right", "both", "center", "middle", "spine", "joint",
    "scalp", "face", "hand", "finger", "heel", "calf", "thigh",
}

CHAR_WORDS = {
    "throbbing", "dull", "sharp", "pressure", "burning", "aching",
    "stabbing", "tight", "squeezing", "pulsing", "constant", "intermittent",
    "shooting", "radiating", "cramping", "gnawing",
}

# Diagnosis safety: minimum supporting symptoms needed
DIAGNOSIS_SAFETY_RULES = {
    "viral fever": {
        "required_any": ["fever"],
        "required_count": 2,
        "supporting": ["fever", "temperature", "body pain", "cold", "cough", "chills", "fatigue"],
    },
    "dengue": {
        "required_any": ["fever"],
        "required_count": 3,
        "supporting": ["fever", "rash", "joint pain", "bone pain", "eye pain", "headache", "platelet"],
    },
    "migraine": {
        "required_any": ["headache"],
        "required_count": 2,
        "supporting": ["headache", "nausea", "vomiting", "light sensitivity", "throbbing", "aura", "one side"],
    },
    "malaria": {
        "required_any": ["fever"],
        "required_count": 3,
        "supporting": ["fever", "chills", "sweating", "rigors", "headache", "body pain", "fatigue"],
    },
}

# ---------------------------------------------------------------------------
# Semantic meaning layer — maps natural human answers to medical values
# ---------------------------------------------------------------------------

# Body-pain words that semantically mean "yes" to any body/muscle pain question
BODY_PAIN_WORDS = [
    "leg pain", "back pain", "knee pain", "joint pain", "muscle pain",
    "body ache", "body pain", "arm pain", "shoulder pain", "neck pain",
    "hip pain", "ankle pain", "wrist pain", "elbow pain", "calf pain",
    "thigh pain", "foot pain", "aching", "aches", "sore muscles",
    "whole body pain", "all over pain",
]

# Question keys that semantically ask about body/muscle pain
BODY_PAIN_KEYS = {"body_pain", "body_ache", "muscle_pain", "has_body_pain", "muscle_ache"}

# Natural duration phrases → normalized value (longest first)
NATURAL_DURATIONS: Dict[str, str] = {
    "today morning and evening": "since this morning",
    "couple of days":            "2 days",
    "couple days":               "2 days",
    "couple of hours":           "2 hours",
    "a few days":                "3 days",
    "few days":                  "3 days",
    "past few days":             "3 days",
    "several days":              "4 days",
    "a few hours":               "few hours",
    "few hours":                 "few hours",
    "since yesterday":           "1 day",
    "from yesterday":            "1 day",
    "yesterday night":           "1 day",
    "since morning":             "since this morning",
    "from morning":              "since this morning",
    "this morning":              "since this morning",
    "today morning":             "since this morning",
    "since evening":             "since this evening",
    "from evening":              "since this evening",
    "this evening":              "since this evening",
    "today evening":             "since this evening",
    "last night":                "since last night",
    "since today":               "since today",
    "from today":                "since today",
    "just started":              "less than 1 hour",
    "just now":                  "less than 1 hour",
}


def infer_medical_meaning(text: str, q_key: str, q_type: str) -> Optional[Tuple[Any, str]]:
    """
    Semantic understanding layer — converts natural human answers into
    structured medical values before strict validation runs.

    Returns (inferred_value, note) when meaning is clear, else None.

    Examples:
      "leg pain"          + body_pain (yesno) -> ("yes", "leg pain")
      "today morning"     + duration          -> ("since this morning", "today morning")
      "muscle ache"       + body_pain (yesno) -> ("yes", "muscle ache")
    """
    tl = TextNormalizer.spell_correct(text).lower().strip()

    # Body-pain semantic understanding
    if q_type == "yesno" and q_key in BODY_PAIN_KEYS:
        for phrase in BODY_PAIN_WORDS:
            if phrase in tl:
                return ("yes", phrase)
        # Single body-part word + pain word also counts
        pain_words   = {"pain", "ache", "aching", "sore", "hurt", "hurts", "painful", "hurting"}
        single_parts = {
            "leg", "back", "knee", "joint", "muscle", "arm", "shoulder",
            "neck", "hip", "ankle", "wrist", "elbow", "calf", "thigh", "foot",
        }
        words = set(tl.split())
        if words & pain_words and words & single_parts:
            matched = next(iter(words & single_parts))
            return ("yes", f"{matched} pain")

    # Natural duration understanding (longest phrase first)
    if q_key == "duration":
        for phrase in sorted(NATURAL_DURATIONS, key=len, reverse=True):
            if phrase in tl:
                return (NATURAL_DURATIONS[phrase], phrase)

    return None


# ---------------------------------------------------------------------------
# Information extractor — reads ANY message for medical facts
# ---------------------------------------------------------------------------

class InfoExtractor:
    """
    Extracts structured medical information from free-text.
    Used before every question decision so already-known fields are skipped.
    """

    # Yes/No pattern
    _YES = YES_VARIANTS
    _NO  = NO_VARIANTS

    # Duration regex: "3 days", "2 weeks", "30 minutes", "since morning" etc.
    _DUR_RE = re.compile(
        r'(\d+)\s*(hour|hr|day|week|month|year|minute|min)s?\b'
        r'|since\s+(morning|evening|night|yesterday|today|last\s+\w+)'
        r'|(few|couple\s+of|several)\s+(hour|day|week|month)s?',
        re.IGNORECASE
    )

    # Severity: "7/10", "7 out of 10", "7", or word
    _SEV_RE = re.compile(r'\b(\d+)\s*(?:/\s*10|out\s+of\s+10)?\b')
    _SEV_WORDS = {
        "very mild": 1, "minimal": 1,
        "mild": 2, "slight": 2, "minor": 2,
        "moderate": 5, "medium": 5,
        "severe": 8, "intense": 8, "sharp": 8,
        "very severe": 10, "unbearable": 10,
    }

    # Temperature: "38.5", "101F", "100.4°F"
    _TEMP_RE = re.compile(r'(\d+\.?\d*)\s*[°]?\s*[cfCF]?\b')

    # Location hints (longest first so more specific phrases match before shorter ones)
    _LOCATION_HINTS = {
        "back of head": "Back of Head",
        "center chest": "Center Chest", "centre chest": "Center Chest",
        "middle chest": "Center Chest", "left chest": "Left Chest",
        "right chest": "Right Chest",
        "lower abdomen": "Lower Abdomen", "lower belly": "Lower Abdomen",
        "lower stomach": "Lower Abdomen", "bottom of stomach": "Lower Abdomen",
        "upper abdomen": "Upper Abdomen", "upper stomach": "Upper Abdomen",
        "lower back": "Lower Back", "upper back": "Upper Back",
        "mid back": "Mid Back", "middle back": "Mid Back",
        "left side": "Left Side", "right side": "Right Side",
        "left flank": "Left Flank", "right flank": "Right Flank",
        "flank": "Flank",
        "forehead": "Forehead", "temples": "Temples", "temple": "Temples",
        "one side": "One Side", "both sides": "Both Sides",
        "entire chest": "Entire Chest", "whole chest": "Entire Chest",
        "groin": "Groin", "pelvic": "Pelvic", "pelvis": "Pelvic",
    }

    # Red-flag phrases that should be stored as yes answers to matching tree keys
    _RED_FLAG_KEYS: Dict[str, List[str]] = {
        "blood_in_urine":  ["blood in urine", "blood in my urine", "urine has blood", "red urine", "pink urine"],
        "blood_in_vomit":  ["blood in vomit", "vomiting blood", "blood when i vomit", "bloody vomit"],
        "blood_stool":     ["blood in stool", "bloody stool", "black stool", "black tarry", "blood in poo"],
        "breathlessness":  ["short of breath", "shortness of breath", "breathless", "difficulty breathing", "can't breathe"],
        "chest_pain":      ["chest pain", "chest ache", "pain in chest"],
        "radiates":        ["radiates to arm", "spreading to arm", "pain in arm", "pain in jaw", "jaw pain", "radiating"],
        "sweating":        ["sweating", "cold sweat", "clammy"],
        "nausea":          ["nausea", "feel sick", "queasy", "nausia"],
        "has_fever":       ["fever", "high temperature", "high temp", "feverish"],
        "has_chills":      ["chills", "shivering", "rigors"],
        "body_pain":       ["body pain", "body ache", "muscle pain", "aching all over"],
        "lower_back_pain": ["lower back pain", "lower back ache", "pain in lower back", "flank pain", "side pain"],
        "burning":         ["burning urination", "burning when i urinate", "pain while urinating", "painful urination"],
        "stiff_neck":      ["stiff neck", "neck stiffness", "neck is stiff"],
        "visual_aura":     ["flashing lights", "blind spots", "zigzag", "aura", "visual disturbance"],
        "light_sensitive": ["light sensitive", "sensitive to light", "light hurts", "photophobia"],
    }

    @classmethod
    def extract(cls, text: str, current_q_key: str = "") -> Dict[str, Any]:
        """
        Parse text and return a dict of ALL fields that can be inferred.
        Keys match patient_answers keys used by the question trees.
        Longer phrases checked before shorter ones to avoid false matches.
        """
        t   = text.strip()
        tl  = TextNormalizer.spell_correct(t).lower()   # spell-correct first
        out: Dict[str, Any] = {}

        # Duration
        dur = cls._extract_duration(tl)
        if dur:
            out["duration"] = dur

        # Severity — ONLY extract when the current question is explicitly asking
        # for a severity number. Never infer severity from adjectives like
        # "severe headache" because that bypasses the 1-10 question entirely.
        if current_q_key in ("severity", "itching_sev"):
            sev = cls._extract_severity(tl, current_q_key)
            if sev is not None:
                out["severity"] = sev

        # Temperature
        temp = cls._extract_temperature(tl)
        if temp:
            out["temperature"] = temp

        # Location — sorted longest-first for specificity
        loc = cls._extract_location(tl)
        if loc:
            out["location"] = loc

        # Red-flag yes/no facts (Rule 5: detect regardless of current question)
        for flag_key, phrases in cls._RED_FLAG_KEYS.items():
            if flag_key not in out:
                for phrase in phrases:
                    if phrase in tl:
                        out[flag_key] = "yes"
                        break

        # Yes/No answer for the current question specifically
        yn = cls._extract_yes_no(tl)
        if yn is not None and current_q_key and current_q_key not in out:
            out[current_q_key] = "yes" if yn else "no"

        # Associated symptoms mentioned inline
        assoc = cls._extract_associated(tl)
        if assoc:
            out["__assoc__"] = assoc

        return out

    @classmethod
    def _extract_duration(cls, tl: str) -> Optional[str]:
        # Natural phrases checked first (longest-first) for specificity
        for phrase in sorted(NATURAL_DURATIONS, key=len, reverse=True):
            if phrase in tl:
                return NATURAL_DURATIONS[phrase]
        m = cls._DUR_RE.search(tl)
        if not m:
            return None
        if m.group(1) and m.group(2):
            return f"{m.group(1)} {m.group(2)}s"
        if m.group(3):
            return f"since {m.group(3)}"
        if m.group(4) and m.group(5):
            return f"{m.group(4)} {m.group(5)}s"
        return None

    @classmethod
    def _extract_severity(cls, tl: str, q_key: str) -> Optional[int]:
        # Only infer severity from a numeric pattern when it's 1-10
        for word in sorted(cls._SEV_WORDS, key=len, reverse=True):
            if word in tl:
                return cls._SEV_WORDS[word]
        m = cls._SEV_RE.search(tl)
        if m:
            try:
                v = int(m.group(1))
                if 1 <= v <= 10:
                    return v
            except ValueError:
                pass
        return None

    @classmethod
    def _extract_temperature(cls, tl: str) -> Optional[str]:
        # Only if "degree", "fever", "temperature" context or F/C present
        if not any(w in tl for w in ["°", " f", " c", "fever", "temp", "degree"]):
            return None
        m = cls._TEMP_RE.search(tl)
        if m:
            val = float(m.group(1))
            if 35 <= val <= 42 or 95 <= val <= 108:
                return m.group(0).strip()
        return None

    @classmethod
    def _extract_location(cls, tl: str) -> Optional[str]:
        # Longest-first matching for specificity
        for phrase, label in sorted(cls._LOCATION_HINTS.items(), key=lambda x: len(x[0]), reverse=True):
            if phrase in tl:
                return label
        loc = TextNormalizer.normalize_location(tl)
        if loc:
            return loc
        return None

    @classmethod
    def _extract_yes_no(cls, tl: str) -> Optional[bool]:
        cleaned = tl.strip().rstrip('.,!')
        # Full match
        if cleaned in cls._YES:
            return True
        if cleaned in cls._NO:
            return False
        # Starts with yes/no
        for v in cls._YES:
            if cleaned.startswith(v + " ") or cleaned.startswith(v + ","):
                return True
        for v in cls._NO:
            if cleaned.startswith(v + " ") or cleaned.startswith(v + ","):
                return False
        return None

    @classmethod
    def _extract_associated(cls, tl: str) -> List[str]:
        """Pick up secondary symptoms mentioned inline."""
        SECONDARY = [
            "shortness of breath", "breathless", "nausea", "vomiting",
            "dizziness", "sweating", "palpitations", "chest tightness",
            "cough", "fever", "chills", "headache", "body ache",
            "fatigue", "weakness", "rash", "itching", "blood in urine",
            "blood in stool", "blurred vision", "neck stiffness",
            "loss of appetite", "weight loss",
        ]
        return [s for s in SECONDARY if s in tl]


# --------------------------------------------------------------------------- #
#  ConversationMemory                                                          #
# --------------------------------------------------------------------------- #

class ConversationMemory:
    def __init__(self):
        self.symptoms: List[str]              = []
        self.extra_symptoms: List[str]        = []
        self.active_symptom: Optional[str] = None
        self.pending_symptoms: List[str] = []
        self.completed_symptoms: List[str] = []
        self.consultation_reports: List[Dict] = []
        self.symptom_category: str            = ""
        self.patient_answers: Dict[str, Any]  = {}
        self.current_stage: str               = "greeting"
        self.primary_diagnosis: Optional[str] = None
        self.confidence: int                  = 0
        self.failed_validations: int          = 0
        self.awaiting_restart_choice: bool    = False
        self.location: Optional[str]          = None
        self.severity: Optional[int]          = None
        self.duration: Optional[Dict]         = None
        self.medical_history: Optional[str]   = None

    def to_dict(self) -> Dict:
        return {
            "symptoms":                self.symptoms,
            "extra_symptoms":          self.extra_symptoms,
            "symptom_category":        self.symptom_category,
            "patient_answers":         self.patient_answers,
            "current_stage":           self.current_stage,
            "primary_diagnosis":       self.primary_diagnosis,
            "confidence":              self.confidence,
            "failed_validations":      self.failed_validations,
            "awaiting_restart_choice": self.awaiting_restart_choice,
            "location":                self.location,
            "severity":                self.severity,
            "duration":                self.duration,
            "medical_history":         self.medical_history,
            "active_symptom": self.active_symptom,
            "pending_symptoms": self.pending_symptoms,
            "completed_symptoms": self.completed_symptoms,
            "consultation_reports": self.consultation_reports,
        }

    def from_dict(self, data: Dict) -> None:
        self.symptoms                = data.get("symptoms", [])
        self.extra_symptoms          = data.get("extra_symptoms", [])
        self.active_symptom          = data.get("active_symptom")
        self.pending_symptoms          = data.get("pending_symptoms", [])
        self.completed_symptoms = data.get("completed_symptoms", [])
        self.consultation_reports = data.get("consultation_reports", [])
        self.symptom_category        = data.get("symptom_category", "")
        self.patient_answers         = data.get("patient_answers", {})
        self.current_stage           = data.get("current_stage", "greeting")
        self.primary_diagnosis       = data.get("primary_diagnosis")
        self.confidence              = data.get("confidence", 0)
        self.failed_validations      = data.get("failed_validations", 0)
        self.awaiting_restart_choice = data.get("awaiting_restart_choice", False)
        self.location                = data.get("location")
        self.severity                = data.get("severity")
        self.duration                = data.get("duration")
        self.medical_history         = data.get("medical_history")

    def reset_to_greeting(self) -> None:
        self.__init__()

    def all_symptoms(self) -> List[str]:
        return list(dict.fromkeys(self.symptoms + self.extra_symptoms))


# --------------------------------------------------------------------------- #
#  EnhancedAIDoctorEngine                                                      #
# --------------------------------------------------------------------------- #

class EnhancedAIDoctorEngine:

    def __init__(self):
        self.diseases         = get_diseases("human")
        self.reasoning_engine = MedicalReasoningEngine(self.diseases)
        self.normalizer       = TextNormalizer()

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def process_message(self, message: str, state: Optional[Dict] = None) -> Dict[str, Any]:
        memory = ConversationMemory()
        if state:
            memory.from_dict(state)

        # Emergency override — always checked first
        emergency_reason = self._detect_emergency(message)
        if emergency_reason:
            memory.current_stage = "diagnosis"
            return {
                "reply":        self._build_emergency_reply(emergency_reason),
                "state":        memory.to_dict(),
                "emergency":    True,
                "is_diagnosis": True,
            }

        if memory.current_stage == "greeting":
            reply, memory = self._handle_greeting(message, memory)
        elif memory.current_stage == "collecting":
            reply, memory = self._handle_collecting(message, memory)
        elif memory.current_stage == "awaiting_more_symptoms":
            reply, memory = self._handle_more_symptoms(
            message,
            memory
            )
        elif memory.current_stage == "diagnosis":
            reply, memory = self._handle_followup(message, memory)
        else:
            # Unknown stage (e.g. legacy local-fallback stage names like
            # "asking_location", "asking_severity") — treat as mid-consultation
            # so we never reset to the greeting welcome message.
            if memory.symptoms:
                memory.current_stage = "collecting"
                reply, memory = self._handle_collecting(message, memory)
            else:
                memory.current_stage = "greeting"
                reply, memory = self._handle_greeting(message, memory)

        return {
            "reply":        reply,
            "state":        memory.to_dict(),
            "emergency":    self._is_emergency_memory(memory),
            "is_diagnosis": memory.current_stage == "diagnosis",
        }

    # ------------------------------------------------------------------ #
    #  Stage: greeting                                                     #
    # ------------------------------------------------------------------ #

    def _handle_greeting(self, message: str, memory: ConversationMemory) -> Tuple[str, ConversationMemory]:
        symptoms = self._extract_symptoms(message)

        if not symptoms:
            return (
                "\U0001f44b Hello! I'm your medical consultation assistant.\n\n"
                "Please describe your main symptom or health concern.\n"
                "For example:\n"
                "\u2022 I have been vomiting since this morning\n"
                "\u2022 I have fever for 2 days\n"
                "\u2022 My chest feels tight\n"
                "\u2022 I have joint pain in my knee\n"
                "\u2022 My skin is very itchy with red patches",
                memory,
            )

        memory.symptoms         = symptoms
        memory.active_symptom = symptoms[0]
        memory.extra_symptoms          = []
        memory.failed_validations      = 0
        memory.awaiting_restart_choice = False

        disease_name = self.normalizer.fuzzy_match_disease(message)
        if disease_name:
            memory.primary_diagnosis = disease_name

        # Extract ALL facts already provided in the opening message
        extracted = InfoExtractor.extract(message)
        assoc = extracted.pop("__assoc__", [])
        for sym in assoc:
            if sym not in memory.all_symptoms():
                memory.extra_symptoms.append(sym)
        self._apply_extracted(extracted, memory, current_q_key="")

        category               = classify_symptom_category(symptoms)
        memory.symptom_category = category
        memory.current_stage    = "collecting"

        category_label = CATEGORY_DISPLAY.get(category, category.replace("_", " ").title())
        sym_display    = ", ".join(s for s in symptoms if not s.startswith("__"))

        next_q = self._get_next_smart_question(memory)
        if next_q is None:
            return self._show_more_symptoms_prompt(memory)

        # Build a doctor-like opening acknowledgement
        opening = self._build_opening_acknowledgement(message, sym_display, extracted)
        reply = f"{opening}\n\n**{next_q['question']}**"
        return reply, memory

    # ------------------------------------------------------------------ #
    #  Stage: collecting answers                                           #
    # ------------------------------------------------------------------ #

    def _handle_collecting(self, message: str, memory: ConversationMemory) -> Tuple[str, ConversationMemory]:
        current_q = self._get_next_smart_question(memory)

        if current_q is None:
            return self._generate_diagnosis(memory)

        # Step 1: Extract ALL information from the message (spell-corrected)
        extracted = InfoExtractor.extract(message, current_q_key=current_q["key"])

        # Step 2: Save extra symptoms mentioned alongside the answer
        assoc = extracted.pop("__assoc__", [])
        for sym in assoc:
            if sym not in memory.all_symptoms():
                memory.extra_symptoms.append(sym)

        # Step 3: Validate the answer for the CURRENT question
        answer, valid, ctx = self._validate_answer(message, current_q)

        if not valid:
            memory.failed_validations += 1
            if memory.failed_validations >= MAX_INVALID_ATTEMPTS:
                # Never ask "Type 1 or 2" — just skip the unanswerable question
                # and move on naturally so the consultation never stalls.
                memory.patient_answers[current_q["key"]] = message.strip() or "not provided"
                memory.failed_validations = 0
                next_q = self._get_next_smart_question(memory)
                if next_q is None:
                    return self._show_more_symptoms_prompt(memory)
                return f"I understand. Let me move on.\n\n**{next_q['question']}**", memory
            return self._build_mismatch_message(current_q, ctx), memory

        # Step 4: Save the validated answer
        memory.patient_answers[current_q["key"]] = answer
        memory.failed_validations = 0
        self._sync_known_values(current_q["key"], answer, memory)

        # If a yesno question received a descriptive answer, also store the
        # raw text as an extra symptom so no information is lost.
        if current_q.get("type") == "yesno" and answer == "yes":
            raw_stripped = message.strip()
            yn_words = YES_VARIANTS | NO_VARIANTS | {"yes", "no"}
            if raw_stripped.lower() not in yn_words and len(raw_stripped) > 3:
                if raw_stripped not in memory.all_symptoms():
                    memory.extra_symptoms.append(raw_stripped)

        # Step 5: Save all other facts extracted from the same message
        self._apply_extracted(extracted, memory, current_q_key=current_q["key"])

        # Step 6: Red-flag check — if a dangerous answer was just given, escalate
        escalation = self._check_red_flag_escalation(memory)
        if escalation:
            return escalation, memory

        # Step 7: Get the next genuinely unanswered question
        next_q = self._get_next_smart_question(memory)
        if next_q is None:
            return self._show_more_symptoms_prompt(memory)

        # Doctor-like acknowledgement before next question
        ack = self._build_acknowledgement(current_q["key"], answer)

        # If semantic inference resolved a body-pain description, add a note
        inferred = infer_medical_meaning(message, current_q["key"], current_q.get("type", "text"))
        if inferred is not None and current_q.get("type") == "yesno" and current_q["key"] in BODY_PAIN_KEYS:
            _, note = inferred
            # Save the specific pain as an extra symptom too
            if note not in memory.all_symptoms():
                memory.extra_symptoms.append(note)
            ack = (
                f"I've noted **{note}**. "
                f"Since that is a form of body pain, I'll record that as yes."
            )
        elif inferred is not None and current_q["key"] == "duration":
            _, note = inferred
            ack = f"Thank you \u2014 I've noted that this started **{answer}**."

        reply = f"{ack}\n\n**{next_q['question']}**"
        return reply, memory

    # ------------------------------------------------------------------ #
    #  Smart question selection — skips already-known fields              #
    # ------------------------------------------------------------------ #

    def _get_next_smart_question(self, memory: ConversationMemory) -> Optional[Dict[str, Any]]:
        """
        Walk the tree and return the next step whose key is NOT already
        present in patient_answers OR resolvable from memory fields.
        Never pre-populate severity from memory — always ask explicitly
        so the user provides a confirmed 1-10 number.
        """
        category  = memory.symptom_category or "default"
        answered  = set(memory.patient_answers.keys())

        # Pre-populate location and duration from top-level memory fields
        # so the tree skips redundant questions for already-known values.
        # Severity is intentionally excluded — must always be confirmed by user.
        if memory.location and "location" not in answered:
            memory.patient_answers["location"] = memory.location
            answered.add("location")
        if memory.duration and "duration" not in answered:
            dur = memory.duration
            memory.patient_answers["duration"] = f"{dur.get('value','')} {dur.get('unit','')}".strip()
            answered.add("duration")

        for step in get_question_tree(category):
            if step["key"] not in answered:
                return step
        return None

    # ------------------------------------------------------------------ #
    #  Apply extracted facts to patient_answers + memory                  #
    # ------------------------------------------------------------------ #

    def _apply_extracted(
        self, extracted: Dict[str, Any], memory: ConversationMemory, current_q_key: str
    ) -> None:
        """Write extracted facts to patient_answers only if not already set."""
        for key, value in extracted.items():
            if key.startswith("__"):
                continue
            if key not in memory.patient_answers:
                memory.patient_answers[key] = value
                self._sync_known_values(key, value, memory)

    # ------------------------------------------------------------------ #
    #  Restart / follow-up handlers                                        #
    # ------------------------------------------------------------------ #

    def _handle_restart_choice(self, message: str, memory: ConversationMemory) -> Tuple[str, ConversationMemory]:
        raw = message.strip().lower()

        if any(w in raw for w in NEW_CONSULT_WORDS) or raw == "2":
            memory.reset_to_greeting()
            return (
                "\u2705 Of course. Let's start fresh.\n\n"
                "\U0001f44b Hello! What brings you in today?",
                memory,
            )

        if any(w in raw for w in RESTART_WORDS) or raw == "1":
            memory.awaiting_restart_choice = False
            memory.failed_validations      = 0
            current_q = self._get_next_smart_question(memory)
            if current_q is None:
                return self._generate_diagnosis(memory)
            hint  = self._get_example_hint(current_q)
            return (
                f"\u2705 No problem, let's continue.\n\n"
                f"**{current_q['question']}**\n\n{hint}",
                memory,
            )

        return (
            "Please let me know how you'd like to proceed:\n\n"
            "\u2022 Type **1** to continue with your current consultation\n"
            "\u2022 Type **2** to start a new consultation",
            memory,
        )

    def _handle_followup(self, message: str, memory: ConversationMemory) -> Tuple[str, ConversationMemory]:
        return (
            "Thank you for getting back to me. For a more thorough evaluation, "
            "I would strongly recommend consulting the recommended specialist in person.\n\n"
            "If you have a new or different symptom you'd like to discuss, "
            "you can start a **New Checkup** at any time.",
            memory,
        )

    # ------------------------------------------------------------------ #
    #  Diagnosis generation                                                #
    # ------------------------------------------------------------------ #

    def _generate_diagnosis(self, memory: ConversationMemory) -> Tuple[str, ConversationMemory]:
        memory.current_stage = "diagnosis"

        context_str       = build_symptom_context(memory.patient_answers)
        enriched_symptoms = list(memory.all_symptoms())

        # ── Save completed symptom report before transitioning ──────────
        if memory.active_symptom and memory.active_symptom not in memory.completed_symptoms:
            # Only save if not already recorded (prevent duplicates)
            already_saved = any(
                r.get("symptom") == memory.active_symptom
                for r in memory.consultation_reports
            )
            if not already_saved:
                memory.consultation_reports.append({
                    "symptom": memory.active_symptom,
                    "answers": memory.patient_answers.copy(),
                })
            memory.completed_symptoms.append(memory.active_symptom)

        # ── Transition to next pending symptom if any remain ────────────
        if memory.pending_symptoms:
            next_symptom = memory.pending_symptoms.pop(0)
            memory.active_symptom  = next_symptom
            memory.patient_answers = {}
            category = classify_symptom_category([next_symptom])
            memory.symptom_category = category
            memory.current_stage    = "collecting"
            next_q = get_next_unanswered_question(category, {})
            question_text = next_q["question"] if next_q else f"Please describe your {next_symptom}."
            reply = (
                f"I've collected enough information about "
                f"**{memory.completed_symptoms[-1]}**.\n\n"
                f"Now let's discuss your **{next_symptom}**.\n\n"
                f"{question_text}"
            )
            return reply, memory

        # ── All symptoms collected — run full diagnosis ─────────────────
        for key, value in memory.patient_answers.items():
            if str(value).lower().strip() in YES_VARIANTS:
                sym = key.replace("_", " ")
                if sym not in enriched_symptoms:
                    enriched_symptoms.append(sym)

        severity_raw = (
            memory.patient_answers.get("severity") or
            memory.patient_answers.get("itching_sev", "")
        )
        try:
            severity_int = int(str(severity_raw).split("/")[0].strip()) if severity_raw else None
        except (ValueError, AttributeError):
            severity_int = None

        duration_raw  = memory.patient_answers.get("duration", "")
        duration_dict = self._parse_duration(str(duration_raw))

        analysis = self.reasoning_engine.analyze_symptoms(
            enriched_symptoms,
            location=memory.patient_answers.get("location") or memory.location,
            severity=severity_int,
            duration=duration_dict,
            history=context_str,
        )

        candidate, conf = self._apply_diagnosis_safety(
            analysis.get("primary_diagnosis"),
            analysis.get("confidence", 0),
            enriched_symptoms,
            memory.patient_answers,
        )
        memory.primary_diagnosis = candidate
        memory.confidence        = conf

        disease_record = find_disease(memory.primary_diagnosis, "human") if memory.primary_diagnosis else None

        diag       = memory.primary_diagnosis or "Inconclusive \u2014 further evaluation needed"
        risk       = (disease_record.get("risk_level", "medium") if disease_record else "medium").upper()
        doctor     = (disease_record.get("doctor_type", "General Physician") if disease_record else "General Physician")
        conf_label = "High" if conf >= 70 else "Medium" if conf >= 40 else "Low"

        risk_emoji = "\U0001f534" if risk == "HIGH" else "\U0001f7e1" if risk == "MEDIUM" else "\U0001f7e2"
        conf_bar   = "\u2588" * (conf // 10) + "\u2591" * (10 - conf // 10)

        L: List[str] = []

        # ── Urgent alert — high risk only ──────────────────────────────
        if risk == "HIGH":
            L += [
                "\U0001f6a8 **Urgent Medical Attention Required**",
                "This assessment suggests a potentially serious condition. Please see a doctor today.",
                "",
            ]

        if conf < 40:
            L += [
                "*Low confidence \u2014 limited information available. Results are indicative only.*",
                "",
            ]

        # ── Consultation Summary ───────────────────────────────────────
        L.append("**Consultation Summary**")
        L.append("")

        sym_display = ", ".join(s.title() for s in memory.all_symptoms() if not s.startswith("__"))
        L.append(f"\u2022 Primary Complaint: {sym_display}")

        loc_val = memory.patient_answers.get("location") or memory.location
        if loc_val:
            L.append(f"\u2022 Location: {loc_val}")
        if duration_raw:
            L.append(f"\u2022 Duration: {duration_raw}")
        if severity_int:
            sev_bar = "\u2588" * severity_int + "\u2591" * (10 - severity_int)
            L.append(f"\u2022 Severity: {severity_int}/10  [{sev_bar}]")
        if memory.patient_answers.get("temperature"):
            L.append(f"\u2022 Temperature: {memory.patient_answers['temperature']}")
        if memory.extra_symptoms:
            L.append(f"\u2022 Also reported: {', '.join(s.title() for s in memory.extra_symptoms)}")

        # Only show meaningful (non-no) collected findings
        findings = [
            (k.replace("_", " ").title(), v)
            for k, v in memory.patient_answers.items()
            if v and str(v).strip()
            and not k.startswith("__")
            and k not in ("location", "duration", "severity", "itching_sev", "temperature")
            and str(v).strip().lower() not in ("no", "none", "not checked", "false")
        ]
        if findings:
            for label, val in findings:
                L.append(f"\u2022 {label}: {val}")

        # ── Most Likely Condition ─────────────────────────────────────
        L.append("")
        L.append("**Most Likely Condition**")
        L.append("")
        L.append(f"{diag}")
        L.append(f"Confidence: {conf}%  [{conf_bar}]  ({conf_label})")
        L.append(f"Risk Level: {risk_emoji} {risk.title()}")

        if risk == "HIGH" or (severity_int and severity_int >= 8):
            action = "Please see a doctor today or go to an urgent care clinic."
        elif risk == "MEDIUM" or (severity_int and severity_int >= 5):
            action = "Schedule an appointment with a doctor within 1\u20132 days."
        else:
            action = "Rest, stay hydrated, and monitor symptoms. See a doctor if symptoms worsen."
        L.append(f"Recommended Action: {action}")

        if disease_record and disease_record.get("description"):
            L.append("")
            L.append(f"*{disease_record['description']}*")

        # ── Other Possible Conditions ─────────────────────────────────
        alternatives = analysis.get("alternative_diagnoses", [])
        alt_list = [a for a in alternatives[:3] if a.get("disease") and a["disease"] != diag]
        if alt_list:
            L.append("")
            L.append("**Other Possible Conditions**")
            L.append("")
            for i, a in enumerate(alt_list, 1):
                cl  = "High" if a["confidence"] >= 70 else "Medium" if a["confidence"] >= 40 else "Low"
                bar = "\u2588" * (a["confidence"] // 10) + "\u2591" * (10 - a["confidence"] // 10)
                L.append(f"{i}. {a['disease']}  \u2014  {a['confidence']}% [{bar}] ({cl})")

        # ── Recommended Tests ─────────────────────────────────────────
        tests = [t for t in (disease_record.get("recommended_tests", []) if disease_record else []) if t]
        if tests:
            L.append("")
            L.append("**Recommended Tests**")
            L.append("")
            for t in tests[:5]:
                L.append(f"\u2022 {t}")

        # ── Medicines ─────────────────────────────────────────────────
        medicines = [m for m in (disease_record.get("medicines", []) if disease_record else []) if m]
        if medicines:
            L.append("")
            L.append("**Medicines**")
            L.append("")
            for m in medicines[:4]:
                L.append(f"\u2022 {m}")
            if risk == "HIGH":
                L.append("")
                L.append("*These medicines require a doctor's prescription.*")
            L.append("")
            L.append("*Always consult a pharmacist or doctor before taking any medicine.*")

        # ── Self Care ─────────────────────────────────────────────────
        precautions   = [p for p in (disease_record.get("precautions",   []) if disease_record else []) if p]
        home_remedies = [r for r in (disease_record.get("home_remedies", []) if disease_record else []) if r]
        care_items    = precautions[:3] + home_remedies[:2] + [
            "Rest adequately and stay well hydrated.",
            "Monitor your symptoms and note any changes.",
        ]
        L.append("")
        L.append("**Self Care**")
        L.append("")
        for item in care_items:
            L.append(f"\u2022 {item}")

        # ── Recommended Diet ──────────────────────────────────────────
        diet = [d for d in (disease_record.get("diet", []) if disease_record else []) if d]
        if diet:
            L.append("")
            L.append("**Recommended Diet**")
            L.append("")
            for item in diet[:5]:
                L.append(f"\u2022 {item}")

        # ── Specialist ────────────────────────────────────────────────
        L.append("")
        L.append("**Recommended Specialist**")
        L.append("")
        L.append(f"\u2022 {doctor}")

        # ── Emergency Warning Signs ───────────────────────────────────
        L.append("")
        L.append("\u26a0\ufe0f **Emergency Warning Signs**")
        L.append("")
        L.append("Call **108 / 112** or go to the nearest emergency room if you notice:")
        L.append("")
        warnings = (
            disease_record.get("emergency_warnings", [])[:4]
            if disease_record and disease_record.get("emergency_warnings")
            else [
                "Chest pain spreading to the arm or jaw",
                "Difficulty breathing or inability to speak",
                "Loss of consciousness or severe confusion",
                "High fever (>104\u00b0F / 40\u00b0C) with a stiff neck",
                "Vomiting blood or blood in stool",
            ]
        )
        for w in warnings:
            L.append(f"\u2022 {w}")

        # ── Medical Disclaimer ────────────────────────────────────────
        L.append("")
        L.append("---")
        L.append("")
        L.append("**Medical Disclaimer**")
        L.append("")
        L += [
            "\u2022 This report is generated by an AI system based on your answers only.",
            "\u2022 It is not a confirmed medical diagnosis.",
            "\u2022 Always consult a licensed healthcare professional for diagnosis and treatment.",
            "\u2022 Do not take any medicines without pharmacist or doctor guidance.",
            "\u2022 In any emergency, call 108 / 112 immediately.",
        ]

        return "\n".join(L), memory

    # ------------------------------------------------------------------ #
    #  Final consolidated report (multi-symptom)                          #
    # ------------------------------------------------------------------ #

    def _generate_final_report(self, memory: ConversationMemory) -> Tuple[str, ConversationMemory]:
        """
        Called when all symptoms have been collected.
        Aggregates all consultation_reports + active symptom answers,
        builds a consolidated symptom list, then reuses existing
        _generate_diagnosis logic.
        """
        # Save active symptom if not yet recorded
        if memory.active_symptom and memory.active_symptom not in memory.completed_symptoms:
            already_saved = any(
                r.get("symptom") == memory.active_symptom
                for r in memory.consultation_reports
            )
            if not already_saved:
                memory.consultation_reports.append({
                    "symptom": memory.active_symptom,
                    "answers": memory.patient_answers.copy(),
                })
            memory.completed_symptoms.append(memory.active_symptom)

        # Aggregate all collected answers across symptoms
        all_answers: Dict[str, Any] = {}
        for report in memory.consultation_reports:
            for k, v in report.get("answers", {}).items():
                if k not in all_answers:
                    all_answers[k] = v
        # Current active answers take precedence
        all_answers.update(memory.patient_answers)
        memory.patient_answers = all_answers

        # Aggregate all symptoms
        all_syms = list(dict.fromkeys(
            memory.completed_symptoms + memory.symptoms + memory.extra_symptoms
        ))
        memory.symptoms = all_syms

        # Build the per-symptom findings header — clean report format
        header_lines: List[str] = []

        if memory.completed_symptoms:
            header_lines.append("**Findings**")
            header_lines.append("")
            header_lines.append(
                "Symptoms assessed: "
                + ", ".join(s.title() for s in memory.completed_symptoms)
            )
            header_lines.append("")

            for report in memory.consultation_reports:
                sym = report.get("symptom", "")
                ans = report.get("answers", {})
                if not sym:
                    continue
                meaningful = [
                    (k, v) for k, v in ans.items()
                    if not k.startswith("__")
                    and str(v).strip()
                    and str(v).strip().lower() not in ("no", "none", "not checked", "false", "")
                ]
                if not meaningful:
                    continue
                header_lines.append(f"*{sym.title()}:*")
                for k, v in meaningful:
                    label = k.replace("_", " ").title()
                    if k in ("severity", "itching_sev"):
                        try:
                            n   = int(str(v).split("/")[0].strip())
                            bar = "\u2588" * n + "\u2591" * (10 - n)
                            header_lines.append(f"\u2022 {label}: {n}/10  [{bar}]")
                            continue
                        except (ValueError, TypeError):
                            pass
                    header_lines.append(f"\u2022 {label}: {v}")
                header_lines.append("")

            header_lines += ["---", ""]

        # Clear transition state so _generate_diagnosis goes straight to the report
        memory.pending_symptoms = []
        memory.active_symptom   = None

        # Run normal diagnosis generation (reuse existing logic)
        diag_reply, memory = self._generate_diagnosis(memory)

        return "\n".join(header_lines) + diag_reply, memory

    # ------------------------------------------------------------------ #
    #  Diagnosis safety guard                                              #
    # ------------------------------------------------------------------ #

    def _apply_diagnosis_safety(
        self, candidate: Optional[str], conf: int,
        symptoms: List[str], answers: Dict[str, Any],
    ) -> Tuple[Optional[str], int]:
        if not candidate:
            return candidate, conf
        key  = candidate.lower().strip()
        rule = DIAGNOSIS_SAFETY_RULES.get(key)
        if not rule:
            return candidate, conf
        all_text = " ".join(symptoms).lower() + " " + " ".join(str(v).lower() for v in answers.values())
        if not any(req in all_text for req in rule["required_any"]):
            return None, 0
        found = sum(1 for s in rule["supporting"] if s in all_text)
        if found < rule["required_count"]:
            return candidate, min(conf, 35)
        return candidate, conf

    # ------------------------------------------------------------------ #
    #  Validation                                                          #
    # ------------------------------------------------------------------ #

    def _validate_answer(self, message: str, step: Dict[str, Any]) -> Tuple[Any, bool, str]:
        q_type = step.get("type", "text")
        key    = step.get("key", "")
        raw    = message.strip()
        ctx    = key.replace("_", " ")

        if not raw:
            return None, False, ctx

        corrected = TextNormalizer.spell_correct(raw)

        # ── Semantic understanding layer (runs BEFORE strict validation) ──
        # Converts natural human answers into structured medical values.
        # e.g. "leg pain" -> yes for body_pain, "today morning" -> duration
        inferred = infer_medical_meaning(raw, key, q_type)
        if inferred is not None:
            value, _note = inferred
            return value, True, ctx

        if q_type == "yesno":
            normalized_yn = TextNormalizer.normalize_yes_no(corrected)
            if normalized_yn == "Yes":
                return "yes", True, ctx
            if normalized_yn == "No":
                return "no", True, ctx
            low = corrected.lower()
            if any(w in low for w in YES_VARIANTS):
                return "yes", True, ctx
            if any(w in low for w in NO_VARIANTS):
                return "no", True, ctx
            # Descriptive answer to a yes/no question (e.g. "burning sensation",
            # "it hurts a lot") — treat as implicit yes and store the raw text
            # as an extra symptom note rather than failing validation.
            if len(raw.strip()) >= 3:
                return "yes", True, ctx
            return raw, False, ctx

        if q_type == "number":
            sev, is_valid = TextNormalizer.parse_severity(corrected)
            if is_valid:
                return sev, True, ctx
            return raw, False, ctx

        if key == "temperature":
            if TextNormalizer.is_context_mismatch(raw, "temperature"):
                return raw, False, ctx
            tl = corrected.lower()
            if re.search(r"\d", corrected):
                return corrected, True, ctx
            if any(w in tl for w in ["not check", "not measure", "don't know",
                                     "unknown", "no thermometer", "didn't check",
                                     "normal", "high", "low", "slight", "mild"]):
                return corrected, True, ctx
            return raw, False, ctx

        if key == "duration":
            # Natural phrases already handled by infer_medical_meaning above.
            dur, is_valid = TextNormalizer.parse_duration(corrected)
            if is_valid:
                return f"{dur['value']} {dur['unit']}", True, ctx
            tl = corrected.lower()
            # Accept any response that contains a number + time unit OR a
            # recognised relative phrase — covers "2 days", "4 days", "1 week",
            # "since yesterday", "since this morning", etc.
            if re.search(
                r'\b\d+\s*(hour|hr|day|week|month|year|minute|min)s?\b'
                r'|(since|from|last|this)\s+(morning|evening|night|week|month|yesterday|today)'
                r'|(few|couple|several|a\s+few)\s+(hour|day|week|month)s?',
                tl
            ):
                return corrected, True, ctx
            # Accept bare numbers as days (e.g. user types just "3")
            if re.fullmatch(r'\d+', tl.strip()):
                return f"{tl.strip()} days", True, ctx
            return raw, False, ctx

        if key in ("location", "which_joints", "affected_areas", "both_eyes", "both_ears"):
            norm_loc = TextNormalizer.normalize_location(corrected)
            if norm_loc:
                return norm_loc, True, ctx
            if set(corrected.lower().split()) & BODY_WORDS:
                return corrected, True, ctx
            if len(corrected.split()) >= 2:
                return corrected, True, ctx
            return raw, False, ctx

        if key == "character":
            if any(w in corrected.lower() for w in CHAR_WORDS):
                return corrected, True, ctx
            if len(corrected.split()) >= 2:
                return corrected, True, ctx
            return raw, False, ctx

        if len(raw) < 2:
            return raw, False, ctx
        return raw, True, ctx

    # ------------------------------------------------------------------ #
    #  Red-flag escalation (mid-consultation)                             #
    # ------------------------------------------------------------------ #

    def _check_red_flag_escalation(self, memory: ConversationMemory) -> Optional[str]:
        """
        After saving an answer, check if a dangerous combination has emerged
        that warrants stopping the normal consultation flow.
        Returns an escalation message string, or None if safe to continue.
        """
        answers = memory.patient_answers
        yes = lambda k: str(answers.get(k, "")).lower() == "yes"

        # Cardiac: chest + radiating + sweating
        if yes("radiates") and yes("sweating"):
            return self._build_escalation_reply(
                "chest pain radiating with sweating",
                "These findings together can be signs of a cardiac event."
            )
        # Chest + breathless
        if yes("breathless") and yes("chest_pain"):
            return self._build_escalation_reply(
                "chest pain with breathlessness",
                "This combination requires urgent evaluation."
            )
        # GI bleed
        if yes("blood_in_vomit") or yes("blood_stool"):
            return self._build_escalation_reply(
                "blood in vomit or stool",
                "This is a red-flag finding that needs prompt medical attention."
            )
        # Neurological: severe headache + stiff neck
        if yes("stiff_neck") and memory.severity and memory.severity >= 7:
            return self._build_escalation_reply(
                "severe headache with neck stiffness",
                "This combination can indicate meningitis and requires urgent evaluation."
            )
        return None

    def _build_escalation_reply(self, reason: str, clinical_note: str) -> str:
        return (
            f"\u26a0\ufe0f **Important Finding — {reason.title()}**\n\n"
            f"{clinical_note}\n\n"
            "I strongly recommend you **seek medical attention as soon as possible** \u2014 "
            "today if you can.\n\n"
            "\u2022 If symptoms are worsening rapidly, call **108 / 112** immediately.\n"
            "\u2022 Do not wait for symptoms to resolve on their own."
        )

    # ------------------------------------------------------------------ #
    #  Doctor-like response builders                                       #
    # ------------------------------------------------------------------ #

    def _build_opening_acknowledgement(
        self, message: str, sym_display: str, extracted: Dict[str, Any]
    ) -> str:
        """
        Build a warm, doctor-like opening that references what was already
        extracted from the patient's first message.
        """
        known_parts = []
        if extracted.get("location"):
            known_parts.append(f"located in the **{extracted['location']}**")
        if extracted.get("duration"):
            known_parts.append(f"lasting **{extracted['duration']}**")
        if extracted.get("severity") is not None:
            known_parts.append(f"rated **{extracted['severity']}/10** in severity")

        base = f"I understand \u2014 you're experiencing **{sym_display}**."
        if known_parts:
            base += " " + "I've noted it is " + ", ".join(known_parts) + "."
        base += "\n\nThank you for that information. I'd like to ask a few more questions to better understand your situation."
        return base

    def _build_acknowledgement(self, key: str, answer: Any) -> str:
        """
        Build a short, natural doctor-like acknowledgement of the given answer.
        Varies by question type to avoid sounding repetitive.
        """
        ACKS_YES = [
            "I see, thank you.",
            "Noted, that's helpful.",
            "Thank you for letting me know.",
            "I understand, thank you.",
            "That information is useful.",
        ]
        ACKS_NO = [
            "Understood.",
            "Good to know, thank you.",
            "Noted.",
            "I see, thank you.",
        ]
        ACKS_GENERIC = [
            "Thank you, I've noted that.",
            "I understand.",
            "That's helpful, thank you.",
            "Noted.",
            "Thank you for explaining that.",
        ]

        # Use a hash of the key to pick consistently but vary across questions
        idx = abs(hash(key)) % 5
        val = str(answer).lower().strip()
        if val == "yes":
            return ACKS_YES[idx % len(ACKS_YES)]
        if val == "no":
            return ACKS_NO[idx % len(ACKS_NO)]
        if key == "severity":
            v = answer if isinstance(answer, int) else 0
            if v >= 8:
                return "I understand \u2014 that sounds quite severe. Thank you for letting me know."
            if v >= 5:
                return "Thank you. A moderate level of discomfort \u2014 I've noted that."
            return "Good to know, thank you."
        if key == "duration":
            return f"Thank you \u2014 I've noted that this has been going on for {answer}."
        if key == "location":
            return f"Noted \u2014 the {answer.lower()} area. Thank you."
        if key == "temperature":
            return "Thank you for that reading. I've made a note of it."
        return ACKS_GENERIC[idx % len(ACKS_GENERIC)]

    # ------------------------------------------------------------------ #
    #  Emergency detection                                                 #
    # ------------------------------------------------------------------ #

    def _detect_emergency(self, text: str) -> str:
        tl = text.lower()
        for kw in EMERGENCY_KEYWORDS:
            if kw in tl:
                return kw
        # Combo detection: each combo element is a phrase — check all present in text
        for combo_phrases, label in EMERGENCY_COMBOS:
            if all(phrase in tl for phrase in combo_phrases):
                return label
        return ""

    def _build_emergency_reply(self, reason: str) -> str:
        return (
            "\u26a0\ufe0f **EMERGENCY WARNING**\n\n"
            f"The symptoms you described ({reason}) may indicate a "
            "**serious or life-threatening condition**.\n\n"
            "**Please seek immediate medical attention right now.**\n\n"
            "\u2022 Call emergency services: **108 / 112**\n"
            "\u2022 Do NOT drive yourself to the hospital\n"
            "\u2022 If you suspect a heart attack and are not allergic to aspirin, "
            "chew one aspirin (325 mg) while waiting for help\n"
            "\u2022 Stay calm and keep someone with you\n\n"
            "Do not continue this consultation. Your safety is the priority."
        )

    def _is_emergency_memory(self, memory: ConversationMemory) -> bool:
        if memory.primary_diagnosis:
            d = find_disease(memory.primary_diagnosis, "human")
            if d and d.get("emergency", False):
                return True
        for key in ("blood_in_vomit", "radiates", "sweating", "breathless"):
            if str(memory.patient_answers.get(key, "")).lower() == "yes":
                if key in ("radiates", "sweating", "breathless"):
                    return True
        return False

    # ------------------------------------------------------------------ #
    #  Message builders                                                    #
    # ------------------------------------------------------------------ #

    def _build_mismatch_message(self, step: Dict[str, Any], context_label: str) -> str:
        q_type   = step.get("type", "text")
        question = step.get("question", "")
        key      = step.get("key", "")
        examples = QUESTION_EXAMPLES.get(key, [])

        lines = [
            "I want to make sure I understand you correctly.",
            "",
            f"I'm asking about **{context_label}**.",
            "",
        ]
        if q_type == "yesno":
            lines.append("Could you please answer with **Yes** or **No**?")
        elif q_type == "number":
            lines.append("Could you rate it on a scale of **1 to 10**?")
            lines.append("For example: 1 = very mild, 5 = moderate, 10 = unbearable")
        elif examples:
            lines.append("For example:")
            for ex in examples[:4]:
                lines.append(f"\u2022 {ex}")
        lines += ["", f"**{question}**"]
        return "\n".join(lines)

    def _build_restart_prompt(self, current_q: Dict[str, Any]) -> str:
        return (
            "I'm finding it a little difficult to collect the information I need.\n\n"
            "That's okay — this happens sometimes. How would you like to proceed?\n\n"
            "\u2022 Type **1** \u2014 Continue where we left off\n"
            "\u2022 Type **2** \u2014 Start a fresh consultation\n\n"
            f"*(I was asking: {current_q['question']})*"
        )

    def _get_example_hint(self, step: Dict[str, Any]) -> str:
        q_type = step.get("type", "text")
        key    = step.get("key", "")
        if q_type == "yesno":
            return "Please reply with **Yes** or **No**."
        if q_type == "number":
            return "Please enter a number between **1 and 10**. For example: 7"
        examples = QUESTION_EXAMPLES.get(key, [])
        if examples:
            return "Examples: " + ", ".join(f"*{e}*" for e in examples[:3])
        return "Please describe in a few words."
    def _show_more_symptoms_prompt(
        self, memory: ConversationMemory
    ) -> Tuple[str, ConversationMemory]:
        """Save the just-completed symptom and ask if there are more."""
        # Save current active symptom report
        if memory.active_symptom and memory.active_symptom not in memory.completed_symptoms:
            already_saved = any(
                r.get("symptom") == memory.active_symptom
                for r in memory.consultation_reports
            )
            if not already_saved:
                memory.consultation_reports.append({
                    "symptom": memory.active_symptom,
                    "answers": memory.patient_answers.copy(),
                })
            memory.completed_symptoms.append(memory.active_symptom)

        completed_names = ", ".join(s.title() for s in memory.completed_symptoms)
        memory.current_stage = "awaiting_more_symptoms"
        return (
            f"I've collected information about **{completed_names}**.\n\n"
            "Do you have any other symptoms you'd like me to assess?\n\n"
            "\u2022 Describe the symptom (e.g. *headache*, *vomiting*)\n"
            "\u2022 Or type **no** to receive your full diagnosis report.",
            memory,
        )

    def _handle_more_symptoms(
        self,
        message: str,
        memory: ConversationMemory,
    ) -> Tuple[str, ConversationMemory]:
        low = message.lower().strip()

        if low in {"no", "none", "nothing", "no more", "that's all", "thats all"}:
            return self._generate_final_report(memory)

        symptoms = self._extract_symptoms(message)

        if symptoms:
            for sym in symptoms:
                if (
                    sym not in memory.pending_symptoms
                    and sym not in memory.completed_symptoms
                    and sym != memory.active_symptom
                ):
                    memory.pending_symptoms.append(sym)

            if not memory.pending_symptoms:
                return self._generate_final_report(memory)

            # Save current active symptom report before transitioning
            if memory.active_symptom and memory.active_symptom not in memory.completed_symptoms:
                already_saved = any(
                    r.get("symptom") == memory.active_symptom
                    for r in memory.consultation_reports
                )
                if not already_saved:
                    memory.consultation_reports.append({
                        "symptom": memory.active_symptom,
                        "answers": memory.patient_answers.copy(),
                    })
                memory.completed_symptoms.append(memory.active_symptom)

            next_symptom = memory.pending_symptoms.pop(0)
            memory.active_symptom   = next_symptom
            category                = classify_symptom_category([next_symptom])
            memory.symptom_category = category
            memory.patient_answers  = {}
            memory.current_stage    = "collecting"
            next_q = get_next_unanswered_question(category, {})
            question_text = next_q["question"] if next_q else f"Please describe your {next_symptom}."
            return (
                f"Let's discuss your **{next_symptom}**.\n\n"
                f"{question_text}",
                memory,
            )

        return (
            "Do you have any other symptoms?\n\n"
            "If yes, please describe them. Otherwise, type **no**.",
            memory,
        )

    # ------------------------------------------------------------------ #
    #  Utilities                                                           #
    # ------------------------------------------------------------------ #

    def _sync_known_values(self, key: str, value: Any, memory: ConversationMemory) -> None:
        if key == "location" and not memory.location:
            memory.location = str(value)
        elif key in ("severity", "itching_sev") and not memory.severity:
            try:
                memory.severity = int(str(value).split("/")[0])
            except (ValueError, AttributeError):
                pass
        elif key == "duration" and not memory.duration:
            memory.duration = self._parse_duration(str(value))

    def _extract_symptoms(self, text: str) -> List[str]:
        normalized = self.normalizer.normalize_text(text)
        body_parts = self.normalizer.extract_body_parts(text)
        symptoms: List[str] = []

        disease = self.normalizer.fuzzy_match_disease(text)
        if disease:
            symptoms.append(disease)

        KEYWORDS = [
            "fever", "vomiting", "nausea", "headache", "chest pain", "chest tightness",
            "stomach pain", "joint pain", "knee pain", "hip pain", "back pain",
            "cough", "cold", "diarrhea", "rash", "itching", "fatigue", "weakness",
            "dizziness", "vertigo", "anxiety", "depression", "insomnia",
            "shortness of breath", "breathless", "wheezing", "sore throat",
            "ear pain", "eye pain", "burning urination", "frequent urination",
            "chills", "body pain", "muscle pain", "neck pain", "palpitations",
            "bloating", "heartburn", "acidity", "loose motion", "skin rash",
            "hives", "stiffness", "weight loss", "blurred vision",
            "increased thirst", "allergy",
        ]
        for kw in KEYWORDS:
            if kw in normalized and kw not in symptoms:
                symptoms.append(kw)
        for part in body_parts:
            if part not in symptoms:
                symptoms.append(part)
        return list(dict.fromkeys(symptoms))

    def _parse_duration(self, text: str) -> Optional[Dict[str, Any]]:
        tl = text.lower()
        for pattern, unit in [
            (r"(\d+)\s*month", "months"),
            (r"(\d+)\s*week",  "weeks"),
            (r"(\d+)\s*day",   "days"),
            (r"(\d+)\s*hour",  "hours"),
        ]:
            m = re.search(pattern, tl)
            if m:
                return {"value": int(m.group(1)), "unit": unit}
        return None


# --------------------------------------------------------------------------- #
#  Backward-compatible wrapper                                                 #
# --------------------------------------------------------------------------- #

class AIDoctorEngine:
    def __init__(self):
        self.engine = EnhancedAIDoctorEngine()

    def process_message(self, message: str, state: Optional[Dict] = None) -> Dict[str, Any]:
        return self.engine.process_message(message, state)
