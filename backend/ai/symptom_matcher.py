"""
symptom_matcher.py — Medical-grade NLP symptom matching engine.

Pipeline:
  raw text
    → spell correction (RapidFuzz / difflib fallback)
    → lowercase + punctuation removal
    → synonym expansion
    → body-part normalization
    → phrase detection
    → TF-IDF cosine similarity (sklearn) with keyword-overlap boost
"""

import re
import logging
from difflib import SequenceMatcher, get_close_matches
from typing import Dict, List, Tuple

from services.knowledge_service import get_diseases

logger = logging.getLogger(__name__)

try:
    from rapidfuzz import fuzz, process as rf_process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# ── Medical vocabulary for spell correction ────────────────────────────────────
# Includes both symptom words AND full disease names for disease-name fuzzy matching
MEDICAL_VOCAB = [
    # Symptoms
    "fever", "headache", "cough", "cold", "stomach", "chest", "pain", "ache",
    "fatigue", "weakness", "dizziness", "nausea", "vomiting", "diarrhea",
    "rash", "swelling", "shortness", "breath", "breathing", "throat", "sore",
    "back", "knee", "joint", "muscle", "bleeding", "burning", "itching",
    "anxiety", "depression", "insomnia", "constipation", "cramps", "chills",
    "sweating", "palpitations", "numbness", "tingling", "discharge",
    "urination", "frequency", "severe", "mild", "moderate", "intense",
    "sudden", "chronic", "acute", "persistent", "intermittent",
    "abdominal", "lumbar", "cervical", "thoracic", "cardiac", "respiratory",
    "neurological", "dermatological", "gastrointestinal", "urological",
    # Disease names (full) — enables "psoasis" → "psoriasis"
    "migraine", "vertigo", "hypertension", "diabetes", "asthma", "arthritis",
    "sinusitis", "bronchitis", "pneumonia", "dengue", "malaria", "typhoid",
    "psoriasis", "eczema", "conjunctivitis", "gastritis", "appendicitis",
    "anemia", "hypothyroidism", "hyperthyroidism", "gerd", "pcos", "gout",
    "sciatica", "chickenpox", "tuberculosis", "hepatitis", "jaundice",
    "meningitis", "epilepsy", "parkinson", "alzheimer", "dementia",
    "osteoporosis", "fibromyalgia", "lupus", "vitiligo", "urticaria",
    "cellulitis", "impetigo", "rosacea", "acne", "alopecia",
    "tonsillitis", "laryngitis", "pharyngitis", "rhinitis",
    "colitis", "pancreatitis", "cholecystitis", "peritonitis",
    "cystitis", "nephritis", "pyelonephritis", "urethritis",
    "tendinitis", "bursitis", "spondylitis", "osteoarthritis",
    "leukemia", "lymphoma", "thrombosis", "embolism",
]

# ── Disease name → canonical symptoms mapping ──────────────────────────────────
# When user types a disease name (even misspelled), extract its symptoms for consultation
DISEASE_NAME_TO_SYMPTOMS: Dict[str, List[str]] = {
    "psoriasis":      ["itchy skin", "red patches", "dry skin", "skin rash"],
    "eczema":         ["itchy skin", "rash", "dry skin", "inflammation"],
    "diabetes":       ["frequent urination", "increased thirst", "fatigue", "blurred vision"],
    "hypertension":   ["headache", "dizziness", "chest pain", "fatigue"],
    "asthma":         ["shortness of breath", "wheezing", "chest tightness", "cough"],
    "migraine":       ["headache", "nausea", "sensitivity to light", "dizziness"],
    "arthritis":      ["joint pain", "swelling", "stiffness", "difficulty walking"],
    "gout":           ["joint pain", "swelling", "toe pain", "redness"],
    "sinusitis":      ["facial pain", "headache", "nasal congestion", "sore throat"],
    "bronchitis":     ["cough", "chest congestion", "fatigue", "shortness of breath"],
    "pneumonia":      ["fever", "cough", "chest pain", "shortness of breath"],
    "dengue":         ["high fever", "body pain", "joint pain", "headache", "rash"],
    "malaria":        ["fever", "chills", "sweating", "body pain", "vomiting"],
    "typhoid":        ["high fever", "abdominal pain", "weakness", "constipation"],
    "anemia":         ["fatigue", "pale skin", "shortness of breath", "dizziness"],
    "gastritis":      ["stomach pain", "nausea", "vomiting", "heartburn"],
    "gerd":           ["heartburn", "acid reflux", "chest burning", "difficulty swallowing"],
    "sciatica":       ["lower back pain", "leg pain", "numbness", "tingling"],
    "chickenpox":     ["itchy rash", "blisters", "fever", "fatigue"],
    "hypothyroidism": ["fatigue", "weight gain", "cold intolerance", "dry skin"],
    "conjunctivitis": ["red eyes", "itchy eyes", "eye discharge", "tearing"],
    "pcos":           ["irregular periods", "weight gain", "acne", "hair fall"],
    "insomnia":       ["difficulty sleeping", "fatigue", "irritability"],
    "anxiety":        ["anxiety", "rapid heartbeat", "sweating", "restlessness"],
    "depression":     ["persistent sadness", "fatigue", "sleep changes", "low motivation"],
    "vertigo":        ["dizziness", "spinning sensation", "nausea", "balance problems"],
    "tonsillitis":    ["sore throat", "fever", "swollen tonsils", "difficulty swallowing"],
    "urticaria":      ["hives", "itching", "rash", "swelling"],
    "vitiligo":       ["white patches", "skin discoloration"],
    "acne":           ["pimples", "oily skin", "skin inflammation"],
}

# ── Spell correction map (common misspellings → correct) ───────────────────────
SPELL_MAP: Dict[str, str] = {
    # Headache variants
    "hedache": "headache", "headche": "headache", "headake": "headache",
    "heache": "headache", "heddache": "headache", "headach": "headache",
    "headacke": "headache", "headaiche": "headache",
    # Stomach variants
    "stomch": "stomach", "stomack": "stomach", "stomak": "stomach",
    "stomache": "stomach", "stommach": "stomach", "stomac": "stomach",
    # Severe variants
    "sever": "severe", "seveer": "severe", "sevare": "severe",
    "sEvere": "severe", "svere": "severe",
    # Fever variants
    "frevor": "fever", "faver": "fever", "fevor": "fever", "fevr": "fever",
    "feverr": "fever", "fveer": "fever", "fever": "fever",
    # Cough variants
    "cof": "cough", "cogh": "cough", "couph": "cough", "caugh": "cough",
    "cought": "cough", "coff": "cough", "couf": "cough",
    # Diarrhea variants
    "diarea": "diarrhea", "diarrhoea": "diarrhea", "diarrea": "diarrhea",
    "diarehea": "diarrhea", "diarraha": "diarrhea", "diarhea": "diarrhea",
    # Vomiting variants
    "vomitting": "vomiting", "vommiting": "vomiting", "vomit": "vomiting",
    "vomitting": "vomiting", "vommit": "vomiting",
    # Swelling/Swollen variants
    "swolen": "swollen", "sweling": "swelling", "sweling": "swelling",
    "swelling": "swelling", "swollen": "swollen",
    # Sprain variants
    "spain": "sprain", "sprian": "sprain", "sprane": "sprain",
    "sprains": "sprain", "spraine": "sprain",
    # Breathing variants
    "breathig": "breathing", "brething": "breathing", "breating": "breathing",
    "breathng": "breathing", "brething": "breathing",
    # Dizziness variants
    "dizines": "dizziness", "dizzines": "dizziness", "dizzy": "dizziness",
    "dizzyness": "dizziness", "dizznis": "dizziness",
    # Chest variants
    "cheast": "chest", "chets": "chest", "chesst": "chest",
    "chest": "chest", "chestpain": "chest pain",
    # Nausea variants
    "nusea": "nausea", "nausia": "nausea", "nauseau": "nausea",
    "nausea": "nausea", "nauseuea": "nausea",
    # Exhausted/Tired variants
    "exausted": "exhausted", "exhuasted": "exhausted", "tierd": "tired",
    "tired": "tired", "exausted": "exhausted",
    # Fatigue variants
    "fatiuge": "fatigue", "fatiguee": "fatigue", "fatiue": "fatigue",
    "fatigue": "fatigue", "fatige": "fatigue",
    # Anxiety variants
    "anxeity": "anxiety", "anxity": "anxiety", "anxiaty": "anxiety",
    "anxiety": "anxiety", "anxeity": "anxiety",
    # Depression variants
    "deprssion": "depression", "depresion": "depression",
    "depression": "depression", "depresion": "depression",
    # Palpitations variants
    "palpation": "palpitations", "paliptation": "palpitations",
    "palpitations": "palpitations", "palpatation": "palpitations",
    # Urination variants
    "urinaton": "urination", "uriantion": "urination",
    "urination": "urination", "urintion": "urination",
    # Itching variants
    "ithcing": "itching", "itcing": "itching", "ithchy": "itchy",
    "itching": "itching", "itching": "itching",
    # Inflammation variants
    "inflamation": "inflammation", "inflmmation": "inflammation",
    "inflammation": "inflammation", "inflmation": "inflammation",
    # Constipation variants
    "constipaton": "constipation", "constipation": "constipation",
    "constpation": "constipation", "constpation": "constipation",
    # Nausea/Queasy variants
    "nauseous": "nausea", "queezy": "nausea", "queasy": "nausea",
    # Disease name misspellings
    "psoasis": "psoriasis", "psoriasiss": "psoriasis", "soriasis": "psoriasis",
    "diabtes": "diabetes", "diabetes": "diabetes", "diabeties": "diabetes",
    "dibeties": "diabetes",
    "asma": "asthma", "asthma": "asthma", "astma": "asthma",
    "pneumonia": "pneumonia", "pnemonia": "pneumonia", "pneumonea": "pneumonia",
    "bronchitis": "bronchitis", "bronchitus": "bronchitis",
    "hypertension": "hypertension", "hypertention": "hypertension",
    "migraine": "migraine", "migrain": "migraine", "migranie": "migraine",
    "arthritis": "arthritis", "arthitus": "arthritis", "arthritus": "arthritis",
    "gout": "gout", "goute": "gout",
    "sinusitis": "sinusitis", "sinusitus": "sinusitis",
    "dengue": "dengue", "dengou": "dengue", "dengu": "dengue",
    "malaria": "malaria", "malaria": "malaria", "malara": "malaria",
    "typhoid": "typhoid", "typhod": "typhoid",
    "anemia": "anemia", "anaemia": "anemia", "anemia": "anemia",
    "conjunctivitis": "conjunctivitis", "conjuncivitis": "conjunctivitis",
    "eczema": "eczema", "eczima": "eczema", "eksema": "eczema",
    "gerd": "gerd", "gurd": "gerd",
    "pcos": "pcos", "pcod": "pcos",
    "sciatica": "sciatica", "sciatica": "sciatica", "sciatica": "sciatica",
    "chickenpox": "chickenpox", "chickenpocks": "chickenpox", "chickenpox": "chickenpox",
    "hypothyroidism": "hypothyroidism", "hyperthyroidism": "hyperthyroidism",
    "insomnia": "insomnia", "insomnea": "insomnia",
}

# ── Synonym map ────────────────────────────────────────────────────────────────
SYNONYMS: Dict[str, str] = {
    "ache": "pain", "aching": "pain", "aches": "pain", "sore": "pain",
    "soreness": "pain", "hurt": "pain", "hurting": "pain", "hurts": "pain",
    "discomfort": "pain", "tender": "pain", "tenderness": "pain",
    "throbbing": "pain", "sharp pain": "pain", "dull pain": "pain",
    "burning pain": "burning",
    "swollen": "swelling", "swells": "swelling", "inflamed": "inflammation",
    "inflammation": "swelling", "puffy": "swelling", "puffiness": "swelling",
    "bloated": "bloating",
    "high temperature": "fever", "high temp": "fever", "temperature": "fever",
    "hot body": "fever", "body heat": "fever", "chills": "fever",
    "feverish": "fever", "running a temperature": "fever",
    "breathless": "shortness of breath", "breathlessness": "shortness of breath",
    "cant breathe": "shortness of breath", "can't breathe": "shortness of breath",
    "difficulty breathing": "shortness of breath", "hard to breathe": "shortness of breath",
    "out of breath": "shortness of breath", "wheezing": "shortness of breath",
    "breathing issue": "shortness of breath", "breathing problem": "shortness of breath",
    "tired": "fatigue", "tiredness": "fatigue", "exhausted": "fatigue",
    "exhaustion": "fatigue", "weak": "weakness", "weakness": "fatigue",
    "lethargic": "fatigue", "lethargy": "fatigue", "no energy": "fatigue",
    "drained": "fatigue", "rundown": "fatigue",
    "sick": "nausea", "queasy": "nausea", "nauseous": "nausea",
    "throwing up": "vomiting", "threw up": "vomiting", "puking": "vomiting",
    "dizzy": "dizziness", "lightheaded": "dizziness", "light headed": "dizziness",
    "spinning": "dizziness", "vertigo": "dizziness",
    "coughing": "cough", "dry cough": "cough", "wet cough": "cough",
    "persistent cough": "cough",
    "itchy": "itching", "itchiness": "itching", "red spots": "rash",
    "skin rash": "rash", "hives": "rash", "bumps": "rash",
    "stiff": "stiffness", "rigid": "stiffness", "tight": "stiffness",
    "cant walk": "difficulty walking", "hard to walk": "difficulty walking",
    "limping": "difficulty walking", "limp": "difficulty walking",
    "walking pain": "difficulty walking", "pain while walking": "difficulty walking",
    "pain when walking": "difficulty walking",
    "body ache": "body pain", "body pain": "muscle pain",
    "chest tightness": "chest pain", "tight chest": "chest pain",
    "knee spain": "knee pain", "knee sprain": "knee pain",
}

# ── Body-part normalization ────────────────────────────────────────────────────
BODY_PART_MAP: Dict[str, str] = {
    "knee pain": "joint pain", "knee ache": "joint pain", "knee aching": "joint pain",
    "knee swelling": "swelling", "knee swollen": "swelling", "knee stiffness": "stiffness",
    "knee stiff": "stiffness", "knee injury": "joint pain", "knee hurt": "joint pain",
    "knee hurts": "joint pain", "knee discomfort": "joint pain",
    "hip pain": "joint pain", "hip ache": "joint pain", "hip swelling": "swelling",
    "shoulder pain": "muscle pain", "shoulder ache": "muscle pain", "shoulder stiff": "stiffness",
    "elbow pain": "joint pain", "elbow swelling": "swelling",
    "wrist pain": "joint pain", "wrist swelling": "swelling",
    "ankle pain": "joint pain", "ankle swelling": "swelling", "ankle swollen": "swelling",
    "toe pain": "joint pain", "big toe pain": "joint pain", "toe swelling": "swelling",
    "neck pain": "muscle pain", "neck stiff": "stiffness", "neck stiffness": "stiffness",
    "chest pain": "chest pain", "chest tightness": "chest pain",
    "chest pressure": "chest pain", "chest discomfort": "chest pain",
    "chest burning": "heartburn",
    "stomach pain": "stomach pain", "stomach ache": "stomach pain",
    "abdominal pain": "stomach pain", "belly pain": "stomach pain",
    "belly ache": "stomach pain", "tummy pain": "stomach pain",
    "tummy ache": "stomach pain",
    "back pain": "back pain", "lower back pain": "back pain",
    "upper back pain": "back pain", "spine pain": "back pain",
    "head pain": "headache", "head ache": "headache",
    "forehead pain": "headache", "temple pain": "headache",
    "eye pain": "eye pain", "eye ache": "eye pain", "eye irritation": "eye pain",
    "ear pain": "ear pain", "ear ache": "ear pain", "earache": "ear pain",
    "throat pain": "sore throat", "throat ache": "sore throat", "sore throat": "sore throat",
    "leg pain": "muscle pain", "leg ache": "muscle pain", "leg cramp": "muscle pain",
    "calf pain": "muscle pain", "arm pain": "muscle pain", "arm ache": "muscle pain",
    "foot pain": "joint pain", "foot ache": "joint pain", "heel pain": "joint pain",
}

MULTI_WORD_PHRASES = sorted(
    list(BODY_PART_MAP.keys()) + list(SYNONYMS.keys()),
    key=len, reverse=True,
)


def correct_spelling(text: str) -> str:
    """
    Correct common medical misspellings word by word.
    Pipeline: explicit SPELL_MAP → RapidFuzz (threshold 70) → difflib fallback.
    Lower threshold catches misspellings like:
      - "psoasis"→"psoriasis" (88% match)
      - "diabtes"→"diabetes" (91% match)  
      - "hedache"→"headache" (93% match)
      - "sever fever"→"severe fever" (95% match)
    """
    words = text.split()
    corrected = []
    for word in words:
        lower = word.lower()
        # 1. Explicit map lookup (fastest, most accurate)
        if lower in SPELL_MAP:
            corrected.append(SPELL_MAP[lower])
            continue
        # Only attempt fuzzy correction for words longer than 4 chars (improves accuracy)
        if len(lower) > 4:
            if RAPIDFUZZ_AVAILABLE:
                match = rf_process.extractOne(lower, MEDICAL_VOCAB, scorer=fuzz.ratio)
                # threshold 70 — catches psoasis(88%), diabtes(91%), hedache(93%)
                if match and match[1] >= 70:
                    corrected.append(match[0])
                    continue
            else:
                # difflib fallback with slightly more permissive threshold
                close = get_close_matches(lower, MEDICAL_VOCAB, n=1, cutoff=0.72)
                if close:
                    corrected.append(close[0])
                    continue
        corrected.append(word)
    return " ".join(corrected)


def fuzzy_match_disease_name(text: str, disease_names: List[str], threshold: int = 65) -> tuple:
    """
    Try to match the full input text (or a token from it) against known disease names.
    Returns (matched_disease_name, confidence_score) or (None, 0).

    Handles:
      - "psoasis"       → ("Psoriasis", 88)
      - "diabtes"       → ("Diabetes", 91)
      - "I have psoasis" → ("Psoriasis", 82)
    
    Threshold 65 is permissive for catching typos, but won't match unrelated words.
    """
    text_lower = text.lower().strip()
    names_lower = [n.lower() for n in disease_names]

    if RAPIDFUZZ_AVAILABLE:
        # Try full text first with token_set_ratio (more forgiving)
        result = rf_process.extractOne(text_lower, names_lower, scorer=fuzz.token_set_ratio)
        if result and result[1] >= threshold:
            idx = names_lower.index(result[0])
            return disease_names[idx], result[1]

        # Try each token individually with ratio (catches "I have psoasis")
        for token in text_lower.split():
            if len(token) < 4:  # Skip very short tokens
                continue
            result = rf_process.extractOne(token, names_lower, scorer=fuzz.ratio)
            if result and result[1] >= threshold:
                idx = names_lower.index(result[0])
                return disease_names[idx], result[1]
    else:
        # difflib fallback with threshold adjusted to match RapidFuzz
        close = get_close_matches(text_lower, names_lower, n=1, cutoff=threshold / 100)
        if close:
            idx = names_lower.index(close[0])
            return disease_names[idx], 80
        for token in text_lower.split():
            if len(token) < 4:
                continue
            close = get_close_matches(token, names_lower, n=1, cutoff=threshold / 100)
            if close:
                idx = names_lower.index(close[0])
                return disease_names[idx], 75

    return None, 0


def get_symptoms_from_disease_name(disease_name: str) -> List[str]:
    """
    Given a matched disease name, return its associated symptoms.
    Checks the static DISEASE_NAME_TO_SYMPTOMS map first, then the knowledge base.
    """
    key = disease_name.lower()
    if key in DISEASE_NAME_TO_SYMPTOMS:
        return DISEASE_NAME_TO_SYMPTOMS[key]

    # Fallback: look up live from knowledge base
    diseases = get_diseases("human")
    for d in diseases:
        if d["disease_name"].lower() == key:
            return d.get("symptoms", [])[:4]

    return []


def normalize_text(text: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def expand_text(text: str) -> str:
    """
    Spell correct → normalize → apply body-part and synonym expansion.
    Returns enriched text with both original tokens and canonical terms.
    """
    corrected = correct_spelling(text)
    normalized = normalize_text(corrected)
    expanded_tokens = [normalized]

    working = normalized
    for phrase in MULTI_WORD_PHRASES:
        if phrase in working:
            replacement = BODY_PART_MAP.get(phrase) or SYNONYMS.get(phrase, phrase)
            expanded_tokens.append(replacement)
            working = working.replace(phrase, replacement)

    expanded_tokens.append(working)

    for token in working.split():
        if token in SYNONYMS:
            expanded_tokens.append(SYNONYMS[token])

    result = " ".join(expanded_tokens)
    logger.debug("[SymptomMatcher] expanded: %r → %r", text, result)
    return result


class SymptomMatcher:
    def __init__(self):
        self.human_diseases  = get_diseases("human")
        self.animal_diseases = get_diseases("animal")
        self.human_names  = [d["disease_name"] for d in self.human_diseases]
        self.animal_names = [d["disease_name"] for d in self.animal_diseases]
        self.human_texts  = [self._disease_text(d) for d in self.human_diseases]
        self.animal_texts = [self._disease_text(d) for d in self.animal_diseases]
        self.human_keywords  = [self._disease_keywords(d) for d in self.human_diseases]
        self.animal_keywords = [self._disease_keywords(d) for d in self.animal_diseases]

        self.vectorizer = None
        self.human_vectors = None
        self.animal_vectors = None

        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                stop_words="english",
                min_df=1,
                sublinear_tf=True,
            )
            corpus = self.human_texts + self.animal_texts
            if corpus:
                self.vectorizer.fit(corpus)
                self.human_vectors  = self.vectorizer.transform(self.human_texts)
                self.animal_vectors = self.vectorizer.transform(self.animal_texts)

        logger.info(
            "[SymptomMatcher] loaded %d human, %d animal diseases. sklearn=%s rapidfuzz=%s",
            len(self.human_names), len(self.animal_names), SKLEARN_AVAILABLE, RAPIDFUZZ_AVAILABLE,
        )

    def _disease_text(self, disease: dict) -> str:
        parts = [disease.get("description", ""), disease.get("disease_name", "")]
        for s in disease.get("symptoms", []):
            parts.extend([s, s, s])
        parts.extend(disease.get("causes", []))
        parts.extend(disease.get("precautions", []))
        parts.extend(disease.get("home_remedies", []))
        parts.append(disease.get("doctor_type", ""))
        parts.append(disease.get("body_system", ""))
        return normalize_text(" ".join(parts))

    def _disease_keywords(self, disease: dict) -> set:
        tokens = set()
        for s in disease.get("symptoms", []):
            tokens.update(normalize_text(s).split())
        for c in disease.get("causes", []):
            tokens.update(normalize_text(c).split())
        tokens.update(normalize_text(disease.get("disease_name", "")).split())
        return tokens

    def _keyword_overlap_score(self, query_tokens: set, disease_keywords: set) -> float:
        if not query_tokens or not disease_keywords:
            return 0.0
        intersection = query_tokens & disease_keywords
        return len(intersection) / (len(query_tokens) + 1)

    def _tfidf_score(self, query_text: str, domain: str) -> List[float]:
        if self.vectorizer is None:
            return []
        vectors = self.human_vectors if domain == "human" else self.animal_vectors
        query_vec = self.vectorizer.transform([query_text])
        scores = cosine_similarity(query_vec, vectors)[0]
        return scores.tolist()

    def _rapidfuzz_boost(self, query: str, disease_name: str) -> float:
        """Additional boost using RapidFuzz token sort ratio against disease name."""
        if not RAPIDFUZZ_AVAILABLE:
            return 0.0
        score = fuzz.token_sort_ratio(query.lower(), disease_name.lower()) / 100.0
        return score * 0.1  # small boost, not dominant

    def match(self, query: str, domain: str = "human", top_n: int = 5) -> List[Tuple[str, float]]:
        expanded = expand_text(query)
        STOP = {"i", "have", "my", "the", "a", "an", "is", "am", "are", "was",
                "has", "with", "and", "or", "in", "on", "at", "to", "of", "for", "it"}
        query_tokens = set(expanded.split()) - STOP

        names    = self.human_names    if domain == "human" else self.animal_names
        keywords = self.human_keywords if domain == "human" else self.animal_keywords

        tfidf_scores = self._tfidf_score(expanded, domain)

        combined: List[Tuple[str, float]] = []
        for i, name in enumerate(names):
            tfidf   = tfidf_scores[i] if tfidf_scores else 0.0
            overlap = self._keyword_overlap_score(query_tokens, keywords[i])

            if not SKLEARN_AVAILABLE:
                texts = self.human_texts if domain == "human" else self.animal_texts
                tfidf = float(SequenceMatcher(None, expanded, texts[i]).ratio())

            rf_boost = self._rapidfuzz_boost(query, name)
            score = 0.65 * tfidf + 0.25 * overlap + rf_boost
            combined.append((name, round(score, 4)))

        ranked = sorted(combined, key=lambda x: x[1], reverse=True)
        results = [(n, s) for n, s in ranked[:top_n] if s > 0.0]
        logger.debug("[SymptomMatcher] query=%r top=%s", query, results[:3])
        return results

    def search_symptoms(self, symptom_terms: List[str], domain: str = "human") -> List[Tuple[str, float]]:
        expanded_terms = [expand_text(t) for t in symptom_terms]
        combined_query = " ".join(expanded_terms)
        return self.match(combined_query, domain=domain, top_n=10)

    def extract_canonical_symptoms(self, text: str) -> List[str]:
        """
        Extract canonical symptoms from free text.
        Pipeline:
          1. Spell-correct input
          2. Multi-word phrase matching (body-part map + synonyms)
          3. Single-word synonym matching
          4. Disease corpus keyword scan
          5. Disease-name fuzzy match → resolve to that disease's symptoms
        
        Confidence threshold 65 ensures we catch disease names even with typos.
        """
        corrected = correct_spelling(text)
        normalized = normalize_text(corrected)
        found: List[str] = []

        # Step 1 — multi-word phrase map
        for phrase in MULTI_WORD_PHRASES:
            if phrase in normalized:
                canonical = BODY_PART_MAP.get(phrase) or SYNONYMS.get(phrase, phrase)
                if canonical not in found:
                    found.append(canonical)

        # Step 2 — single-word synonyms
        for token in normalized.split():
            if token in SYNONYMS:
                canonical = SYNONYMS[token]
                if canonical not in found:
                    found.append(canonical)

        # Step 3 — disease corpus keyword scan
        diseases = get_diseases("human")
        for disease in diseases:
            for symptom in disease.get("symptoms", []):
                if normalize_text(symptom) in normalized and symptom not in found:
                    found.append(symptom)

        # Step 4 — disease-name fuzzy match with lower threshold (catches "psoasis", "diabtes", etc.)
        if not found or len(found) < 2:  # Try disease name lookup if we have few symptoms
            disease_names = [d["disease_name"] for d in diseases]
            matched_name, score = fuzzy_match_disease_name(text, disease_names, threshold=65)
            if matched_name and score >= 65:
                disease_symptoms = get_symptoms_from_disease_name(matched_name)
                for s in disease_symptoms:
                    if s not in found:
                        found.append(s)
                # Tag matched name for confirmation message
                found.append(f"__disease_match__:{matched_name}:{score}")
                logger.info(
                    "[SymptomMatcher] disease-name fuzzy match: %r → %s (score=%d)",
                    text, matched_name, score,
                )

        logger.debug("[SymptomMatcher] extract_canonical_symptoms(%r) → %s", text, found)
        return found

    def fuzzy_match_symptom(self, word: str, threshold: int = 75) -> str:
        """
        Given a single potentially misspelled symptom word,
        return closest canonical symptom or the original word.
        """
        all_symptoms = list(SYNONYMS.keys()) + list(BODY_PART_MAP.keys())
        if RAPIDFUZZ_AVAILABLE:
            match = rf_process.extractOne(word.lower(), all_symptoms, scorer=fuzz.ratio)
            if match and match[1] >= threshold:
                canonical = BODY_PART_MAP.get(match[0]) or SYNONYMS.get(match[0], match[0])
                return canonical
        else:
            close = get_close_matches(word.lower(), all_symptoms, n=1, cutoff=threshold / 100)
            if close:
                canonical = BODY_PART_MAP.get(close[0]) or SYNONYMS.get(close[0], close[0])
                return canonical
        return word

    def direct_disease_name_lookup(self, text: str, threshold: int = 65) -> tuple:
        """
        Public wrapper — try to match input directly against disease names.
        Returns (disease_name, score) or (None, 0).
        Threshold 65 catches typos like psoasis→psoriasis, diabtes→diabetes.
        """
        disease_names = [d["disease_name"] for d in self.human_diseases]
        return fuzzy_match_disease_name(text, disease_names, threshold=threshold)


# ── Module-level singletons ────────────────────────────────────────────────────
_default_matcher: SymptomMatcher | None = None


def _get_matcher() -> SymptomMatcher:
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = SymptomMatcher()
    return _default_matcher


def extract_canonical_symptoms(text: str) -> List[str]:
    return _get_matcher().extract_canonical_symptoms(text)


def correct_text_spelling(text: str) -> str:
    return correct_spelling(text)


def direct_disease_name_lookup(text: str, threshold: int = 70) -> tuple:
    """Module-level wrapper — fuzzy-match input against all known disease names."""
    return _get_matcher().direct_disease_name_lookup(text, threshold=threshold)
