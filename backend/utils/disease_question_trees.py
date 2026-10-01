"""
disease_question_trees.py — Symptom-category-driven dynamic question flows.

Exports used by enhanced_ai_doctor_engine.py:
  classify_symptom_category(symptoms)         → category string
  get_next_unanswered_question(cat, answered) → next step dict or None
  build_symptom_context(answers)              → readable context string
  get_question_tree(category)                 → list of step dicts

Each step dict:
  key      — state key to store answer under
  question — text shown to user
  type     — 'yesno' | 'number' | 'text'
  required — bool
"""

from typing import Dict, List, Optional, Any

# ── Symptom → Category mapping ────────────────────────────────────────────────
SYMPTOM_CATEGORY_MAP: Dict[str, str] = {
    # GI / Vomiting
    "vomiting": "vomiting", "nausea": "vomiting", "throwing up": "vomiting",
    "puking": "vomiting", "ulti": "vomiting",

    # Fever
    "fever": "fever", "high temperature": "fever", "jvaram": "fever",
    "bukhar": "fever", "chills": "fever", "feverish": "fever",

    # Chest
    "chest pain": "chest_pain", "chest tightness": "chest_pain",
    "chest pressure": "chest_pain", "heart pain": "chest_pain",
    "tight chest": "chest_pain", "seena dard": "chest_pain",

    # Joint
    "joint pain": "joint_pain", "knee pain": "joint_pain",
    "arthritis": "joint_pain", "hip pain": "joint_pain",
    "ankle pain": "joint_pain", "elbow pain": "joint_pain",
    "wrist pain": "joint_pain", "shoulder pain": "joint_pain",
    "stiffness": "joint_pain", "swollen joint": "joint_pain",

    # Skin
    "rash": "skin", "itching": "skin", "itchy skin": "skin",
    "psoriasis": "skin", "eczema": "skin", "skin rash": "skin",
    "red patches": "skin", "hives": "skin", "skin problem": "skin",
    "bumps": "skin", "urticaria": "skin",
    "allergy": "skin", "allergic reaction": "skin", "skin allergy": "skin",
    "food allergy": "skin", "drug allergy": "skin",
    "dust allergy": "skin", "pollen allergy": "skin",

    # Back
    "back pain": "back_pain", "lower back pain": "back_pain",
    "spine pain": "back_pain", "backache": "back_pain",
    "lumbar pain": "back_pain", "kamar dard": "back_pain",

    # Headache
    "headache": "headache", "migraine": "headache", "head pain": "headache",
    "tala noppi": "headache", "sir dard": "headache",

    # Respiratory
    "cough": "respiratory", "shortness of breath": "respiratory",
    "breathing difficulty": "respiratory", "wheezing": "respiratory",
    "breathless": "respiratory", "khasi": "respiratory",
    "cold": "respiratory", "sore throat": "respiratory", "sneezing": "respiratory",
    "breathlessness": "respiratory",

    # Stomach
    "stomach pain": "stomach_pain", "abdominal pain": "stomach_pain",
    "gastric pain": "stomach_pain", "heartburn": "stomach_pain",
    "acidity": "stomach_pain", "bloating": "stomach_pain",
    "diarrhea": "stomach_pain", "loose motion": "stomach_pain",
    "pet dard": "stomach_pain", "indigestion": "stomach_pain",

    # Urinary
    "frequent urination": "urinary", "burning urination": "urinary",
    "painful urination": "urinary", "blood in urine": "urinary",
    "urinary pain": "urinary",

    # Mental health
    "anxiety": "mental_health", "depression": "mental_health",
    "insomnia": "mental_health", "stress": "mental_health",
    "panic": "mental_health", "low mood": "mental_health",

    # Dizziness
    "dizziness": "dizziness", "dizzy": "dizziness", "vertigo": "dizziness",
    "lightheaded": "dizziness", "spinning": "dizziness", "chakkar": "dizziness",
    "fainting": "dizziness", "loss of consciousness": "dizziness",

    # Fatigue
    "fatigue": "fatigue", "weakness": "fatigue", "tired": "fatigue",
    "exhaustion": "fatigue", "no energy": "fatigue", "thakaan": "fatigue",

    # Neurological / Emergency
    "confusion": "headache", "seizure": "headache",

    # Eye
    "eye pain": "eye", "red eyes": "eye", "itchy eyes": "eye",
    "blurry vision": "eye", "eye discharge": "eye",

    # Ear
    "ear pain": "ear", "earache": "ear", "hearing loss": "ear",
    "ear discharge": "ear",

    # Diabetes
    "frequent thirst": "diabetes_symptoms", "increased thirst": "diabetes_symptoms",
    "excessive urination": "diabetes_symptoms", "blurred vision": "diabetes_symptoms",
    "slow healing": "diabetes_symptoms",
}

# ── Question trees ────────────────────────────────────────────────────────────
QUESTION_TREES: Dict[str, List[Dict[str, Any]]] = {

    "vomiting": [
        {"key": "vomit_count",    "question": "How many times have you vomited in the last 24 hours?",                            "type": "text",   "required": True},
        {"key": "has_fever",      "question": "Do you have a fever along with the vomiting? (yes / no)",                          "type": "yesno",  "required": True},
        {"key": "stomach_pain",   "question": "Do you have any stomach pain or cramps? (yes / no)",                               "type": "yesno",  "required": True},
        {"key": "has_diarrhea",   "question": "Are you also having diarrhea or loose stools? (yes / no)",                         "type": "yesno",  "required": True},
        {"key": "blood_in_vomit", "question": "Have you noticed any blood in your vomit? (yes / no)",                            "type": "yesno",  "required": True},
        {"key": "recent_food",    "question": "Did you eat outside food, street food, or anything unusual in the last 24 hours? (yes / no)", "type": "yesno", "required": True},
        {"key": "keep_fluids",    "question": "Are you able to keep liquids down, or do you vomit immediately after drinking? (yes = can keep down / no = vomiting liquids too)", "type": "yesno", "required": True},
        {"key": "duration",       "question": "How long have these symptoms been going on? (e.g., 2 hours, 1 day)",               "type": "text",   "required": True},
    ],

    "fever": [
        {"key": "temperature",    "question": "Have you measured your temperature? What was the reading? (e.g., 101°F / 38.5°C — or say 'not checked')", "type": "text",  "required": True},
        {"key": "has_chills",     "question": "Are you experiencing chills or shivering? (yes / no)",                                                    "type": "yesno", "required": True},
        {"key": "body_pain",      "question": "Do you have body aches or muscle pain with the fever? (yes / no)",                                        "type": "yesno", "required": True},
        {"key": "has_cough",      "question": "Do you have a cough or sore throat? (yes / no)",                                                          "type": "yesno", "required": True},
        {"key": "breathing_diff", "question": "Do you have any difficulty breathing or breathlessness? (yes / no)",                                      "type": "yesno", "required": True},
        {"key": "recent_travel",  "question": "Have you recently traveled to a different city, state, or country? (yes / no)",                            "type": "yesno", "required": True},
        {"key": "mosquito_exp",   "question": "Have you been in an area with mosquitoes or been bitten recently? (yes / no)",                             "type": "yesno", "required": True},
        {"key": "duration",       "question": "How long have you had the fever? (e.g., since this morning, 2 days, 5 days)",                              "type": "text",  "required": True},
    ],

    "chest_pain": [
        {"key": "location",        "question": "Where exactly is the chest pain — center, left side, right side, or entire chest?",                    "type": "text",   "required": True},
        {"key": "radiates",        "question": "Does the pain spread to your left arm, jaw, neck, or back? (yes / no)",                                "type": "yesno",  "required": True},
        {"key": "sweating",        "question": "Are you sweating unusually or feeling clammy? (yes / no)",                                             "type": "yesno",  "required": True},
        {"key": "breathless",      "question": "Do you feel breathless or short of breath along with the chest pain? (yes / no)",                      "type": "yesno",  "required": True},
        {"key": "worse_breathing", "question": "Does the pain get worse when you breathe deeply or move? (yes / no)",                                  "type": "yesno",  "required": True},
        {"key": "cardiac_history", "question": "Do you have a personal or family history of heart disease, high blood pressure, or high cholesterol? (yes / no)", "type": "yesno", "required": True},
        {"key": "duration",        "question": "How long has this chest pain been present? (e.g., 10 minutes, 2 hours, 1 day)",                        "type": "text",   "required": True},
        {"key": "severity",        "question": "On a scale of 1–10, how severe is the chest pain right now?",                                          "type": "number", "required": True},
    ],

    "joint_pain": [
        {"key": "which_joints",    "question": "Which joints are affected? (e.g., knee, hip, shoulder, wrist, ankle, or multiple)",                    "type": "text",   "required": True},
        {"key": "swelling",        "question": "Is there any visible swelling or warmth around the joint? (yes / no)",                                 "type": "yesno",  "required": True},
        {"key": "morning_stiff",   "question": "Do you have stiffness especially in the morning that lasts more than 30 minutes? (yes / no)",          "type": "yesno",  "required": True},
        {"key": "injury_history",  "question": "Was there any recent injury, fall, or physical trauma to the affected joint? (yes / no)",               "type": "yesno",  "required": True},
        {"key": "mobility",        "question": "Is your mobility limited — can you walk, bend, or move the joint normally? (yes = normal / no = limited)", "type": "yesno", "required": True},
        {"key": "multiple_joints", "question": "Are multiple joints affected at the same time? (yes / no)",                                            "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long have you had this joint pain? (e.g., 3 days, 2 weeks, 3 months)",                             "type": "text",   "required": True},
        {"key": "severity",        "question": "Rate the joint pain on a scale of 1–10 (1 = mild, 10 = unbearable):",                                  "type": "number", "required": True},
    ],

    "skin": [
        {"key": "allergy_type",    "question": "What kind of problem are you experiencing — itching, rash, red patches, hives, or something else?",    "type": "text",   "required": True},
        {"key": "itching_sev",     "question": "How severe is the itching? Rate from 1–10 (1 = mild, 10 = unbearable):",                               "type": "number", "required": True},
        {"key": "red_patches",     "question": "Do you have red, inflamed patches or raised skin lesions? (yes / no)",                                 "type": "yesno",  "required": True},
        {"key": "scaling",         "question": "Is there any scaling, peeling, or flaking of the skin? (yes / no)",                                    "type": "yesno",  "required": True},
        {"key": "affected_areas",  "question": "Which areas of your body are affected? (e.g., scalp, elbows, face, hands, full body)",                 "type": "text",   "required": True},
        {"key": "known_trigger",   "question": "Do you know what triggers it — a food, medicine, soap, pollen, dust, or stress? (describe or say 'unknown')", "type": "text", "required": True},
        {"key": "breathing_diff",  "question": "Are you having any difficulty breathing, throat swelling, or swelling of the face/tongue? (yes / no — IMPORTANT for safety)", "type": "yesno", "required": True},
        {"key": "family_history",  "question": "Does anyone in your family have psoriasis, eczema, or similar skin/allergy conditions? (yes / no)",    "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long have you had this skin problem? (e.g., 1 day, 1 week, months)",                               "type": "text",   "required": True},
    ],

    "back_pain": [
        {"key": "location",        "question": "Where is the back pain — lower back, upper back, or entire spine?",                                    "type": "text",   "required": True},
        {"key": "radiates_leg",    "question": "Does the pain radiate down your leg or into the buttocks? (yes / no)",                                 "type": "yesno",  "required": True},
        {"key": "numbness",        "question": "Do you have any numbness, tingling, or weakness in your legs? (yes / no)",                             "type": "yesno",  "required": True},
        {"key": "injury",          "question": "Did the pain start after lifting something heavy, a fall, or sudden movement? (yes / no)",              "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long have you had this back pain? (e.g., 2 days, 1 week, 3 months)",                               "type": "text",   "required": True},
        {"key": "severity",        "question": "Rate your back pain from 1–10 (1 = mild, 10 = severe):",                                               "type": "number", "required": True},
        {"key": "worse_sitting",   "question": "Is the pain worse after sitting for long periods or after waking up? (yes / no)",                      "type": "yesno",  "required": False},
    ],

    "headache": [
        {"key": "location",        "question": "Where exactly is the headache — forehead, temples, back of head, one side, or all over?",              "type": "text",   "required": True},
        {"key": "character",       "question": "How would you describe it — throbbing, pressure-like, sharp, or dull?",                                "type": "text",   "required": True},
        {"key": "visual_aura",     "question": "Do you see flashing lights, blind spots, or zigzag lines before the headache? (yes / no)",             "type": "yesno",  "required": True},
        {"key": "nausea",          "question": "Do you have nausea or vomiting with the headache? (yes / no)",                                         "type": "yesno",  "required": True},
        {"key": "light_sensitive", "question": "Are you sensitive to light or sound during the headache? (yes / no)",                                  "type": "yesno",  "required": True},
        {"key": "stiff_neck",      "question": "Do you have a stiff neck or neck pain along with the headache? (yes / no)",                            "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long has this headache lasted? (e.g., 2 hours, since morning, 3 days)",                            "type": "text",   "required": True},
        {"key": "severity",        "question": "Rate the headache from 1–10 (1 = mild, 10 = worst headache of your life):",                            "type": "number", "required": True},
    ],

    "respiratory": [
        {"key": "cough_type",      "question": "Is it a dry cough or are you bringing up mucus/phlegm?",                                               "type": "text",   "required": True},
        {"key": "mucus_color",     "question": "If there is mucus, what color is it? (clear, white, yellow, green, bloody — or say 'no mucus')",       "type": "text",   "required": False},
        {"key": "breathlessness",  "question": "Do you feel short of breath or breathless — at rest or during activity? (yes / no)",                   "type": "yesno",  "required": True},
        {"key": "chest_pain",      "question": "Do you have any chest pain or tightness when coughing or breathing? (yes / no)",                       "type": "yesno",  "required": True},
        {"key": "has_fever",       "question": "Do you have a fever? (yes / no)",                                                                      "type": "yesno",  "required": True},
        {"key": "smoker",          "question": "Do you smoke or are you regularly exposed to dust or chemical fumes? (yes / no)",                       "type": "yesno",  "required": True},
        {"key": "asthma_history",  "question": "Do you have a history of asthma or any known allergies? (yes / no)",                                   "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long have you had these respiratory symptoms? (e.g., 2 days, 1 week)",                              "type": "text",   "required": True},
    ],

    "stomach_pain": [
        {"key": "location",        "question": "Where exactly is the pain — upper abdomen, lower abdomen, around the navel, or all over?",             "type": "text",   "required": True},
        {"key": "nausea",          "question": "Do you have nausea or vomiting? (yes / no)",                                                           "type": "yesno",  "required": True},
        {"key": "diarrhea",        "question": "Do you have diarrhea or loose stools? (yes / no)",                                                     "type": "yesno",  "required": True},
        {"key": "heartburn",       "question": "Do you have heartburn, acidity, or a burning sensation? (yes / no)",                                   "type": "yesno",  "required": True},
        {"key": "blood_stool",     "question": "Have you noticed any blood in your stool or black tarry stools? (yes / no)",                           "type": "yesno",  "required": True},
        {"key": "worse_after_eat", "question": "Is the pain worse after eating? (yes / no)",                                                           "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long have you had this stomach pain? (e.g., since morning, 2 days, 1 week)",                       "type": "text",   "required": True},
        {"key": "severity",        "question": "Rate the stomach pain from 1–10 (1 = mild discomfort, 10 = severe):",                                  "type": "number", "required": True},
    ],

    "urinary": [
        {"key": "frequency",       "question": "Approximately how many times do you urinate per day?",                                                 "type": "text",   "required": True},
        {"key": "burning",         "question": "Do you feel burning or pain while urinating? (yes / no)",                                              "type": "yesno",  "required": True},
        {"key": "blood_urine",     "question": "Have you noticed any blood or reddish color in your urine? (yes / no)",                                "type": "yesno",  "required": True},
        {"key": "cloudy_urine",    "question": "Is your urine cloudy, dark, or has an unusual smell? (yes / no)",                                      "type": "yesno",  "required": True},
        {"key": "lower_back_pain", "question": "Do you have lower back or flank pain (pain on the side below your ribs)? (yes / no)",                  "type": "yesno",  "required": True},
        {"key": "has_fever",       "question": "Do you have a fever along with these urinary symptoms? (yes / no)",                                    "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long have you had these urinary symptoms? (e.g., 1 day, 3 days, 1 week)",                          "type": "text",   "required": True},
    ],

    "mental_health": [
        {"key": "main_symptom",    "question": "What bothers you most — anxiety/worry, low mood/sadness, difficulty sleeping, or something else?",     "type": "text",   "required": True},
        {"key": "duration",        "question": "How long have you been experiencing these feelings? (e.g., 2 weeks, 3 months)",                         "type": "text",   "required": True},
        {"key": "sleep_quality",   "question": "How is your sleep — difficulty falling asleep, staying asleep, or waking too early?",                   "type": "text",   "required": True},
        {"key": "palpitations",    "question": "Do you experience a racing heart, chest tightness, or palpitations? (yes / no)",                       "type": "yesno",  "required": True},
        {"key": "daily_function",  "question": "Are these symptoms affecting your daily work, relationships, or activities? (yes / no)",                "type": "yesno",  "required": True},
        {"key": "triggers",        "question": "Can you identify any triggers — work stress, family issues, trauma, or major life events? (describe or say 'none')", "type": "text", "required": False},
        {"key": "severity",        "question": "Rate the overall severity of how you're feeling from 1–10 (1 = mild, 10 = overwhelming):",             "type": "number", "required": True},
    ],

    "dizziness": [
        {"key": "type",            "question": "Do you feel like the room is spinning (vertigo), or just lightheaded/unsteady?",                       "type": "text",   "required": True},
        {"key": "on_standing",     "question": "Does dizziness happen when you stand up quickly? (yes / no)",                                          "type": "yesno",  "required": True},
        {"key": "ear_symptoms",    "question": "Do you have ringing in the ears, ear fullness, or hearing changes? (yes / no)",                        "type": "yesno",  "required": True},
        {"key": "nausea",          "question": "Do you have nausea or vomiting with the dizziness? (yes / no)",                                        "type": "yesno",  "required": True},
        {"key": "headache",        "question": "Do you have a headache along with the dizziness? (yes / no)",                                          "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long does each dizzy episode last, and how long has this been happening?",                          "type": "text",   "required": True},
        {"key": "severity",        "question": "Rate the dizziness from 1–10 (1 = mild, 10 = unable to stand):",                                       "type": "number", "required": True},
    ],

    "fatigue": [
        {"key": "duration",        "question": "How long have you been feeling unusually tired or weak? (e.g., 1 week, 1 month)",                      "type": "text",   "required": True},
        {"key": "sleep_hours",     "question": "How many hours of sleep do you get per night, and is it restful?",                                     "type": "text",   "required": True},
        {"key": "weight_change",   "question": "Have you noticed any unexplained weight loss recently? (yes / no)",                                    "type": "yesno",  "required": True},
        {"key": "breathless",      "question": "Do you feel breathless or short of breath even with mild activity? (yes / no)",                        "type": "yesno",  "required": True},
        {"key": "pale_skin",       "question": "Have others noticed you look pale, or do you feel cold easily? (yes / no)",                            "type": "yesno",  "required": True},
        {"key": "diet",            "question": "How would you describe your diet — balanced, vegetarian, irregular meals, or poor?",                    "type": "text",   "required": False},
        {"key": "severity",        "question": "Rate the fatigue from 1–10 (1 = slightly tired, 10 = unable to function):",                            "type": "number", "required": True},
    ],

    "eye": [
        {"key": "both_eyes",       "question": "Is one eye or both eyes affected?",                                                                    "type": "text",   "required": True},
        {"key": "discharge",       "question": "Is there any discharge, crusting, or watering from the eye? (yes / no)",                               "type": "yesno",  "required": True},
        {"key": "vision_change",   "question": "Has your vision become blurry or changed recently? (yes / no)",                                        "type": "yesno",  "required": True},
        {"key": "light_sensitive", "question": "Are you sensitive to light? (yes / no)",                                                               "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long have you had this eye problem? (e.g., 2 days, 1 week)",                                       "type": "text",   "required": True},
        {"key": "severity",        "question": "Rate the eye discomfort from 1–10:",                                                                   "type": "number", "required": True},
    ],

    "ear": [
        {"key": "both_ears",       "question": "Is one ear or both ears affected?",                                                                    "type": "text",   "required": True},
        {"key": "discharge",       "question": "Is there any discharge, fluid, or blood from the ear? (yes / no)",                                     "type": "yesno",  "required": True},
        {"key": "hearing_loss",    "question": "Have you noticed any decrease in hearing? (yes / no)",                                                 "type": "yesno",  "required": True},
        {"key": "ringing",         "question": "Do you hear ringing, buzzing, or other sounds in the ear? (yes / no)",                                 "type": "yesno",  "required": True},
        {"key": "has_fever",       "question": "Do you have a fever or sore throat along with ear pain? (yes / no)",                                   "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long have you had this ear problem?",                                                               "type": "text",   "required": True},
        {"key": "severity",        "question": "Rate the ear pain from 1–10:",                                                                         "type": "number", "required": True},
    ],

    "diabetes_symptoms": [
        {"key": "thirst",          "question": "Are you drinking much more water than usual? (yes / no)",                                              "type": "yesno",  "required": True},
        {"key": "urination_freq",  "question": "Are you urinating much more frequently, including at night? (yes / no)",                               "type": "yesno",  "required": True},
        {"key": "fatigue",         "question": "Do you feel unusually tired or weak? (yes / no)",                                                      "type": "yesno",  "required": True},
        {"key": "blurred_vision",  "question": "Has your vision become blurry recently? (yes / no)",                                                   "type": "yesno",  "required": True},
        {"key": "slow_healing",    "question": "Do cuts or wounds take longer than usual to heal? (yes / no)",                                         "type": "yesno",  "required": True},
        {"key": "family_history",  "question": "Does anyone in your family have diabetes? (yes / no)",                                                 "type": "yesno",  "required": True},
        {"key": "weight_loss",     "question": "Have you had unexplained weight loss despite eating normally? (yes / no)",                              "type": "yesno",  "required": True},
        {"key": "duration",        "question": "How long have you been noticing these symptoms? (e.g., 1 month, 6 months)",                            "type": "text",   "required": True},
    ],

    "default": [
        {"key": "description",     "question": "Can you describe your main symptom in a bit more detail?",                                             "type": "text",   "required": True},
        {"key": "location",        "question": "Where in your body do you feel this most? (e.g., chest, stomach, head, legs)",                         "type": "text",   "required": True},
        {"key": "severity",        "question": "On a scale of 1–10, how severe is this? (1 = mild, 10 = unbearable)",                                   "type": "number", "required": True},
        {"key": "duration",        "question": "How long have you had this symptom? (e.g., 2 hours, 3 days, 1 week)",                                   "type": "text",   "required": True},
        {"key": "other_symptoms",  "question": "Are there any other symptoms — fever, nausea, pain elsewhere? (describe or say 'none')",                 "type": "text",   "required": False},
        {"key": "medications",     "question": "Are you taking any medications or do you have any known medical conditions? (describe or say 'none')",   "type": "text",   "required": False},
    ],
}

# Preserved for any legacy imports
QUESTION_STAGES = ["location", "severity", "duration", "history"]

# Priority order for category classification
_PRIORITY = [
    "chest_pain", "vomiting", "urinary", "skin", "joint_pain",
    "back_pain", "headache", "respiratory", "stomach_pain",
    "fever", "dizziness", "fatigue", "mental_health", "eye", "ear",
    "diabetes_symptoms",
]


def classify_symptom_category(symptoms: List[str]) -> str:
    """
    Map a list of detected symptoms to the best question-tree category.
    Returns the highest-priority category that has at least one match.
    """
    sym_lower = [s.lower() for s in symptoms]
    scores: Dict[str, int] = {}
    for sym in sym_lower:
        # Exact match first
        cat = SYMPTOM_CATEGORY_MAP.get(sym)
        if cat:
            scores[cat] = scores.get(cat, 0) + 2
        else:
            # Substring match for phrases like "severe fever", "high fever"
            for keyword, category in SYMPTOM_CATEGORY_MAP.items():
                if keyword.lower() in sym:
                    scores[category] = scores.get(category, 0) + 1

    if not scores:
        return "default"

    for cat in _PRIORITY:
        if scores.get(cat, 0) > 0:
            return cat

    return max(scores, key=lambda c: scores[c])


def get_question_tree(category: str) -> List[Dict[str, Any]]:
    """Return the ordered question list for a category."""
    return QUESTION_TREES.get(category, QUESTION_TREES["default"])


def get_next_unanswered_question(
    category: str,
    answered_keys: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Walk the question tree and return the first step whose key
    has not been answered yet. Returns None when all are answered.
    """
    for step in get_question_tree(category):
        value = answered_keys.get(step["key"])
        if value in (None, "", []):
            return step
    return None


def build_symptom_context(answers: Dict[str, Any]) -> str:
    """
    Convert the collected patient_answers dict into a readable string
    for the medical reasoning engine.
    """
    parts = []
    for key, value in answers.items():
        if value is None:
            continue
        label = key.replace("_", " ").title()
        parts.append(f"{label}: {value}")
    return "; ".join(parts)


# ── Backward-compatible class ─────────────────────────────────────────────────

class DiseaseQuestionTree:
    """Legacy class kept for any old imports."""

    @staticmethod
    def get_questions_for_disease(disease_name: str, stage: str) -> List[str]:
        generic = {
            "location": ["Where exactly do you feel this symptom?"],
            "severity": ["On a scale of 1-10, how severe is this?"],
            "duration": ["How long have you had this symptom?"],
            "history":  ["Do you have any relevant medical history or medications?"],
        }
        return generic.get(stage, [])
    
    @staticmethod
    def validate_vomit_count(response: str):
        pass

    @staticmethod
    def get_generic_questions(stage: str) -> List[str]:
        return DiseaseQuestionTree.get_questions_for_disease("", stage)

    @staticmethod
    def validate_sleep_hours(response: str):
        pass

    @staticmethod
    def validate_frequency(response: str):
        pass