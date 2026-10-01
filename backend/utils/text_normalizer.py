"""
text_normalizer.py - Advanced text normalization with spell correction and fuzzy matching.

Features:
  - Medical spell correction
  - Fuzzy matching for disease names
  - Text expansion and synonym resolution
  - Body part normalization
"""

import re
from typing import Dict, List, Tuple
from difflib import SequenceMatcher, get_close_matches

# Rule 14: Location normalization map
LOCATION_NORMALIZATIONS = {
    "lower": "Lower Abdomen",
    "lower abdomen": "Lower Abdomen",
    "lower belly": "Lower Abdomen",
    "lower stomach": "Lower Abdomen",
    "lower abdominal": "Lower Abdomen",
    "bottom stomach": "Lower Abdomen",
    "bottom belly": "Lower Abdomen",
    "low abdomen": "Lower Abdomen",
    "low belly": "Lower Abdomen",
    "low stomach": "Lower Abdomen",
    "upper": "Upper Abdomen",
    "upper abdomen": "Upper Abdomen",
    "upper stomach": "Upper Abdomen",
    "upper belly": "Upper Abdomen",
    "upper abdominal": "Upper Abdomen",
    "top stomach": "Upper Abdomen",
    "top belly": "Upper Abdomen",
    "left": "Left",
    "lft": "Left",
    "left side": "Left",
    "left part": "Left",
    "right": "Right",
    "rgt": "Right",
    "right side": "Right",
    "right part": "Right",
    "both sides": "Both Sides",
    "both": "Both Sides",
    "center chest": "Center Chest",
    "centre chest": "Center Chest",
    "middle chest": "Center Chest",
    "mid chest": "Center Chest",
    "left chest": "Left Chest",
    "right chest": "Right Chest",
    "lower back": "Lower Back",
    "upper back": "Upper Back",
    "mid back": "Mid Back",
    "middle back": "Mid Back",
}

# Rule 14: Yes / No normalization sets
YES_VARIANTS = {"yes", "y", "yep", "yeah", "yah", "sure", "correct", "true", "affirmative", "aye", "ok", "okay", "yup", "haan", "avunu"}
NO_VARIANTS  = {"no", "n", "nope", "nah", "nay", "false", "negative", "not", "never", "nahi", "ledu"}

# Medical spell correction dictionary
SPELL_CORRECTIONS = {
    "hedache": "headache", "headche": "headache", "headake": "headache",
    "heache": "headache", "heddache": "headache", "headach": "headache",
    "stomch": "stomach", "stomack": "stomach", "stomak": "stomach",
    "stomache": "stomach", "stommach": "stomach", "stumach": "stomach",
    "sever": "severe", "seveer": "severe", "sevare": "severe", "sever": "severe",
    "frevor": "fever", "faver": "fever", "fevor": "fever", "fevr": "fever",
    "cof": "cough", "cogh": "cough", "couph": "cough", "caugh": "cough",
    "diarea": "diarrhea", "diarrhoea": "diarrhea", "diarrea": "diarrhea",
    "vomitting": "vomiting", "vommiting": "vomiting",
    "swolen": "swollen", "sweling": "swelling", "swolen": "swollen",
    "spain": "sprain", "sprian": "sprain", "sprane": "sprain",
    "breathig": "breathing", "brething": "breathing", "breating": "breathing",
    "dizines": "dizziness", "dizzines": "dizziness",
    "cheast": "chest", "chets": "chest", "chesst": "chest",
    "nusea": "nausea", "nausia": "nausea", "nauseau": "nausea",
    "exausted": "exhausted", "exhuasted": "exhausted", "tierd": "tired",
    "fatiuge": "fatigue", "fatiguee": "fatigue", "fatiue": "fatigue",
    "anxeity": "anxiety", "anxity": "anxiety", "anxiaty": "anxiety",
    "deprssion": "depression", "depresion": "depression",
    "palpation": "palpitations", "paliptation": "palpitations",
    "urinaton": "urination", "uriantion": "urination",
    "ithcing": "itching", "itcing": "itching", "ithchy": "itchy",
    "inflamation": "inflammation", "inflmmation": "inflammation",
    "constipaton": "constipation",
    "psoasis": "psoriasis", "psoriasis": "psoriasis",
    "diabtes": "diabetes", "diebetes": "diabetes",
    "hypertention": "hypertension", "hypertention": "hypertension",
    "arthitus": "arthritis", "arthritus": "arthritis",
    "sinusitus": "sinusitis",
    "bronchus": "bronchitis", "bronchitus": "bronchitis",
    "pneumoni": "pneumonia",
    "eczima": "eczema", "exema": "eczema",
    "gerd": "gerd", "gastro-esophageal": "gerd",
    "dengue": "dengue", "dengei": "dengue",
    "malaria": "malaria", "malaira": "malaria",
    "typhoid": "typhoid", "thyphoid": "typhoid",
    "chickenpox": "chickenpox", "chickepox": "chickenpox",
    "urticaria": "urticaria", "hives": "hives",
    "vitiligo": "vitiligo",
    # Severity
    "modrate": "moderate", "moderat": "moderate", "modrte": "moderate",
    "seveer": "severe", "sevre": "severe", "sevare": "severe",
    # Fever / temperature
    "feveer": "fever", "fver": "fever",
    "temprature": "temperature", "temperture": "temperature", "temparature": "temperature",
    # Duration abbreviations (Rule 17)
    "dys": "days", "dy": "day",
    "wks": "weeks", "wk": "week",
    "mns": "months",
    "hrs": "hours",
}

# Disease name variants and misspellings
DISEASE_VARIANTS = {
    "psoriasis": ["psoriasis", "psoasis", "psoriasis"],
    "eczema": ["eczema", "eczima", "exema"],
    "diabetes": ["diabetes", "diabtes", "diebetes"],
    "hypertension": ["hypertension", "hypertention", "high blood pressure"],
    "asthma": ["asthma", "ashma"],
    "arthritis": ["arthritis", "arthitus", "arthritus"],
    "migraine": ["migraine", "mirgane"],
    "sinusitis": ["sinusitis", "sinusitus", "sinus"],
    "bronchitis": ["bronchitis", "bronchus", "bronchitus"],
    "pneumonia": ["pneumonia", "pneumoni"],
    "dengue": ["dengue", "dengei"],
    "malaria": ["malaria", "malaira"],
    "typhoid": ["typhoid", "thyphoid"],
    "chickenpox": ["chickenpox", "chickepox"],
    "conjunctivitis": ["conjunctivitis", "pink eye", "pink-eye"],
    "gerd": ["gerd", "gastro-esophageal reflux"],
    "pcos": ["pcos", "poly cystic ovary syndrome"],
    "gout": ["gout"],
    "sciatica": ["sciatica", "sciatic"],
    "urticaria": ["urticaria", "hives"],
    "vitiligo": ["vitiligo"],
    "acne": ["acne", "pimples"],
    "rosacea": ["rosacea"],
    "alopecia": ["alopecia", "hair loss"],
    "tonsillitis": ["tonsillitis", "tonsilitis"],
    "laryngitis": ["laryngitis"],
    "pharyngitis": ["pharyngitis"],
    "rhinitis": ["rhinitis"],
    "colitis": ["colitis"],
    "pancreatitis": ["pancreatitis"],
    "cholecystitis": ["cholecystitis"],
    "gastritis": ["gastritis"],
    "cystitis": ["cystitis"],
    "nephritis": ["nephritis"],
    "pyelonephritis": ["pyelonephritis"],
}

# Symptom synonyms
SYNONYMS = {
    "ache": "pain", "aches": "pain", "aching": "pain",
    "sore": "pain", "soreness": "pain",
    "hurt": "pain", "hurts": "pain", "hurting": "pain",
    "discomfort": "pain",
    "tender": "pain", "tenderness": "pain",
    "throbbing": "pain",
    "burning pain": "burning",
    "high temperature": "fever", "high temp": "fever", "temp": "fever",
    "body heat": "fever", "feverish": "fever",
    "hot body": "fever", "running a fever": "fever",
    "swollen": "swelling", "swells": "swelling", "puffy": "swelling", "puffiness": "swelling",
    "inflamed": "swelling", "inflammation": "swelling",
    "bloated": "bloating", "bloating": "bloating",
    "breathless": "shortness of breath", "breathlessness": "shortness of breath",
    "cant breathe": "shortness of breath", "can't breathe": "shortness of breath",
    "difficulty breathing": "shortness of breath",
    "hard to breathe": "shortness of breath", "out of breath": "shortness of breath",
    "tired": "fatigue", "tiredness": "fatigue", "exhausted": "fatigue", "exhaustion": "fatigue",
    "weak": "weakness",
    "stiffness": "stiffness", "stiff": "stiffness",
    "nauseous": "nausea", "queezy": "nausea", "queasy": "nausea",
    "throwing up": "vomiting", "threw up": "vomiting", "puking": "vomiting", "sick": "nausea",
}

# Body part mappings and aliases
BODY_PARTS = {
    "head": ["head", "skull", "scalp"],
    "face": ["face", "facial"],
    "eye": ["eye", "eyes", "ocular", "ophthalmic"],
    "ear": ["ear", "ears", "aural"],
    "nose": ["nose", "nasal", "nosal"],
    "mouth": ["mouth", "oral"],
    "throat": ["throat", "pharynx", "pharyngeal"],
    "tongue": ["tongue", "lingual"],
    "neck": ["neck", "cervical", "nape"],
    "shoulder": ["shoulder", "shoulders", "shoulder blade", "scapula"],
    "arm": ["arm", "arms", "upper arm", "forearm", "bicep", "tricep"],
    "elbow": ["elbow", "elbows"],
    "wrist": ["wrist", "wrists"],
    "hand": ["hand", "hands", "palm"],
    "finger": ["finger", "fingers", "digit"],
    "chest": ["chest", "breast", "thorax", "thoracic"],
    "breast": ["breast", "breasts", "mammary"],
    "back": ["back", "dorsal", "spinal"],
    "spine": ["spine", "spinal", "vertebrae"],
    "waist": ["waist", "lumbar"],
    "abdomen": ["abdomen", "abdominal", "belly", "stomach"],
    "liver": ["liver", "hepatic"],
    "kidney": ["kidney", "kidneys", "renal"],
    "bladder": ["bladder", "urinary"],
    "stomach": ["stomach", "gastric", "gastro"],
    "intestine": ["intestine", "intestines", "bowel", "bowels", "colon"],
    "hip": ["hip", "hips"],
    "pelvis": ["pelvis", "pelvic"],
    "thigh": ["thigh", "thighs"],
    "knee": ["knee", "knees", "patellar"],
    "leg": ["leg", "legs"],
    "ankle": ["ankle", "ankles"],
    "foot": ["foot", "feet", "pedal"],
    "toe": ["toe", "toes"],
    "skin": ["skin", "dermis", "dermal"],
    "joint": ["joint", "joints", "articulation"],
    "muscle": ["muscle", "muscles", "muscular"],
    "bone": ["bone", "bones", "skeletal"],
    "nerve": ["nerve", "nerves", "neural", "neurological"],
    "heart": ["heart", "cardiac", "cardio"],
    "lung": ["lung", "lungs", "pulmonary", "respiratory"],
}

# Severity levels
SEVERITY_LEVELS = {
    "very mild": 1, "minimal": 1,
    "mild": 2, "slight": 2, "minor": 2,
    "moderate": 5, "medium": 5, "fair": 5,
    "severe": 8, "intense": 8, "sharp": 8,
    "very severe": 10, "critical": 10, "unbearable": 10,
}

# Duration patterns
DURATION_PATTERNS = {
    "minutes": ["minute", "minutes", "min", "mins", "m"],
    "hours": ["hour", "hours", "hr", "hrs", "h"],
    "days": ["day", "days", "d"],
    "weeks": ["week", "weeks", "w"],
    "months": ["month", "months", "mo"],
    "years": ["year", "years", "y"],
}


# Symptom keywords for context-mismatch detection (Rule 16)
_SYMPTOM_WORDS = {
    "pain", "ache", "fever", "cough", "headache", "nausea", "vomit",
    "diarrhea", "rash", "swelling", "fatigue", "heart", "chest",
    "stomach", "back", "cold", "flu",
}


class TextNormalizer:
    """Normalize medical text with spell correction and fuzzy matching."""

    @staticmethod
    def spell_correct(text: str) -> str:
        """Correct common medical spelling mistakes (Rule 15). Fixes duration abbreviations too."""
        # Fix abbreviated duration units first (Rule 17)
        text = re.sub(r'\b(\d+)\s*dys\b',  r'\1 days',   text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d+)\s*dy\b',   r'\1 day',    text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d+)\s*wks\b',  r'\1 weeks',  text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d+)\s*wk\b',   r'\1 week',   text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d+)\s*hrs\b',  r'\1 hours',  text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d+)\s*mns\b',  r'\1 months', text, flags=re.IGNORECASE)
        words = text.split()
        corrected = []
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            corrected.append(SPELL_CORRECTIONS.get(clean_word, word))
        return " ".join(corrected)

    @staticmethod
    def normalize_location(text: str) -> str:
        """Rule 14: Normalize location answer to standard medical value."""
        cleaned = text.lower().strip()
        if cleaned in LOCATION_NORMALIZATIONS:
            return LOCATION_NORMALIZATIONS[cleaned]
        for key in sorted(LOCATION_NORMALIZATIONS, key=len, reverse=True):
            if key in cleaned:
                return LOCATION_NORMALIZATIONS[key]
        return ""

    @staticmethod
    def normalize_yes_no(text: str) -> str:
        """Rule 14: Normalize yes/no answer. Returns 'Yes', 'No', or empty string."""
        cleaned = text.lower().strip().rstrip('.,!')
        if cleaned in YES_VARIANTS:
            return "Yes"
        if cleaned in NO_VARIANTS:
            return "No"
        for v in YES_VARIANTS:
            if cleaned.startswith(v + " ") or cleaned.startswith(v + ","):
                return "Yes"
        for v in NO_VARIANTS:
            if cleaned.startswith(v + " ") or cleaned.startswith(v + ","):
                return "No"
        return ""

    @staticmethod
    def is_context_mismatch(response: str, question_type: str) -> bool:
        """Rule 16: Detect if answer is clearly off-topic for the question type."""
        r = response.lower().strip()
        has_symptom = any(w in r for w in _SYMPTOM_WORDS)
        if question_type == "temperature":
            return has_symptom and not bool(re.search(r'\d', r))
        if question_type == "yes_no":
            return TextNormalizer.normalize_yes_no(response) == "" and has_symptom
        return False

    @staticmethod
    def expand_synonyms(text: str) -> str:
        """Expand synonyms to canonical forms."""
        result = text.lower()
        for synonym, canonical in SYNONYMS.items():
            result = re.sub(r'\b' + re.escape(synonym) + r'\b', canonical, result)
        return result

    @staticmethod
    def normalize_body_part(part: str) -> str:
        """Normalize body part name to canonical form."""
        part_lower = part.lower().strip()
        for canonical, aliases in BODY_PARTS.items():
            if part_lower in aliases:
                return canonical
        return part_lower

    @staticmethod
    def extract_body_parts(text: str) -> List[str]:
        """Extract all mentioned body parts from text."""
        text_lower = text.lower()
        parts = set()
        for canonical, aliases in BODY_PARTS.items():
            for alias in aliases:
                if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                    parts.add(canonical)
        return list(parts)

    @staticmethod
    def parse_severity(text: str) -> Tuple[int, bool]:
        """
        Parse severity after spell-correction (Rule 15/17).
        Accepts numbers 1-10, '7/10', word forms like 'modrate'.
        Returns: (severity_score, is_valid)
        """
        corrected  = TextNormalizer.spell_correct(text)
        text_lower = corrected.lower().strip()

        # Numeric: "7", "7/10", "7 out of 10"
        m = re.search(r'\b(\d+)\s*(?:/\s*10|out of 10)?\b', text_lower)
        if m:
            try:
                num = int(m.group(1))
                if 1 <= num <= 10:
                    return num, True
            except ValueError:
                pass

        # Word form (longest match first)
        for level in sorted(SEVERITY_LEVELS, key=len, reverse=True):
            if level in text_lower:
                return SEVERITY_LEVELS[level], True

        return 0, False

    @staticmethod
    def parse_duration(text: str) -> Tuple[dict, bool]:
        """
        Parse duration after spell-correction (Rule 15/17).
        Accepts '5 dys', '2wks', '3 days', etc.
        Returns: (duration_dict, is_valid)
        """
        corrected  = TextNormalizer.spell_correct(text)
        text_lower = corrected.lower().strip()

        numbers = re.findall(r'\d+', text_lower)
        if not numbers:
            return {}, False

        value = int(numbers[0])

        for unit, keywords in DURATION_PATTERNS.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    return {"value": value, "unit": unit}, True

        return {}, False

    @staticmethod
    def fuzzy_match_disease(text: str, threshold: float = 0.70) -> str:
        """
        Fuzzy match disease name from input text.
        Returns canonical disease name (lowercase key) or empty string.

        Tokenises the input so "I have psoasis" correctly matches "psoriasis".
        """
        text_lower = text.lower().strip()
        tokens = text_lower.split()

        for canonical, variants in DISEASE_VARIANTS.items():
            for variant in variants:
                # 1. Full-text match
                ratio = SequenceMatcher(None, text_lower, variant).ratio()
                if ratio >= threshold:
                    return canonical
                # 2. Token-level match (catches "I have psoasis")
                for token in tokens:
                    if len(token) < 4:
                        continue
                    token_ratio = SequenceMatcher(None, token, variant).ratio()
                    if token_ratio >= threshold:
                        return canonical

        return ""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Apply full normalization pipeline."""
        # Step 1: Spell correction (Rule 15 — always first)
        text = TextNormalizer.spell_correct(text)
        # Step 2: Synonym expansion
        text = TextNormalizer.expand_synonyms(text)
        # Step 3: Lowercase and clean
        text = text.lower().strip()
        # Step 4: Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text

    @staticmethod
    def extract_severity_from_text(text: str) -> int:
        """Extract severity number from user response."""
        severity, is_valid = TextNormalizer.parse_severity(text)
        return severity if is_valid else 0

    @staticmethod
    def extract_duration_from_text(text: str) -> dict:
        """Extract duration from user response."""
        duration, is_valid = TextNormalizer.parse_duration(text)
        return duration if is_valid else {}
