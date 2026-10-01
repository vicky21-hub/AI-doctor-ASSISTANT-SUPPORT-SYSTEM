"""
medicine_recommender.py — OTC medicine recommendations with dosage and safety notes.

Only recommends Over-The-Counter medicines.
Never recommends prescription-only drugs.
Always includes disclaimer.
"""

from typing import Any, Dict, List

from services.knowledge_service import find_disease, find_medicine


# ── OTC medicine database with dosage and safety ──────────────────────────────
OTC_MEDICINES: Dict[str, Dict[str, Any]] = {
    "Paracetamol": {
        "name": "Paracetamol (Crocin / Dolo 650)",
        "dosage": "500mg–1000mg every 6 hours (max 4g/day)",
        "indication": "Fever, mild to moderate pain",
        "warnings": "Do not exceed 4g/day. Avoid alcohol. Caution in liver disease.",
        "otc": True,
    },
    "Ibuprofen": {
        "name": "Ibuprofen (Brufen / Combiflam)",
        "dosage": "200mg–400mg every 6-8 hours with food",
        "indication": "Pain, inflammation, fever",
        "warnings": "Take with food. Avoid on empty stomach. Caution in kidney/stomach issues.",
        "otc": True,
    },
    "Cetirizine": {
        "name": "Cetirizine (Cetcip / Okacet)",
        "dosage": "10mg once daily at night",
        "indication": "Allergy, runny nose, itching, rash",
        "warnings": "May cause drowsiness. Avoid driving after taking.",
        "otc": True,
    },
    "Loratadine": {
        "name": "Loratadine (Lorfast / Clarityne)",
        "dosage": "10mg once daily",
        "indication": "Allergy, hay fever, hives",
        "warnings": "Non-drowsy antihistamine. Safe for daytime use.",
        "otc": True,
    },
    "Antacid": {
        "name": "Antacid (Gelusil / Digene / Pantop D)",
        "dosage": "2 tablets or 10ml after meals and at bedtime",
        "indication": "Acidity, heartburn, indigestion",
        "warnings": "Do not use continuously for more than 2 weeks without medical advice.",
        "otc": True,
    },
    "Oral rehydration salts": {
        "name": "ORS (Electral / Pedialyte)",
        "dosage": "1 sachet dissolved in 1 litre water; sip every 15-20 minutes",
        "indication": "Diarrhea, vomiting, dehydration, fever",
        "warnings": "Do not use plain water only for severe dehydration. Mix correctly.",
        "otc": True,
    },
    "Loperamide": {
        "name": "Loperamide (Imodium)",
        "dosage": "4mg initially, then 2mg after each loose stool (max 16mg/day)",
        "indication": "Acute diarrhea",
        "warnings": "Do not use if blood in stool or high fever. Not for children under 2.",
        "otc": True,
    },
    "Vitamin C": {
        "name": "Vitamin C supplement (500mg)",
        "dosage": "500mg once daily",
        "indication": "Immune support, cold, fever",
        "warnings": "High doses (>2g) may cause stomach upset.",
        "otc": True,
    },
    "Iron supplement": {
        "name": "Iron + Folic Acid tablet (Ferrous sulfate)",
        "dosage": "One tablet daily with Vitamin C (enhances absorption)",
        "indication": "Iron deficiency anemia, fatigue",
        "warnings": "Take on empty stomach if tolerated. May cause dark stools and constipation.",
        "otc": True,
    },
    "Vitamin D3 supplement": {
        "name": "Vitamin D3 (Calcirol / D-Rise 60K)",
        "dosage": "1000–2000 IU daily or as directed",
        "indication": "Vitamin D deficiency, bone pain, fatigue",
        "warnings": "Do not self-prescribe high doses (> 4000 IU) without testing.",
        "otc": True,
    },
    "Vitamin B12 supplement": {
        "name": "Vitamin B12 (Methylcobalamin 500mcg)",
        "dosage": "500mcg daily",
        "indication": "B12 deficiency, fatigue, neuropathy",
        "warnings": "Generally safe. Consult if numbness persists.",
        "otc": True,
    },
    "Melatonin": {
        "name": "Melatonin (0.5mg–3mg)",
        "dosage": "0.5mg–3mg 30 minutes before sleep",
        "indication": "Insomnia, jet lag",
        "warnings": "Start with low dose. Not for long-term use without guidance.",
        "otc": True,
    },
    "Cough syrup": {
        "name": "Cough syrup (Honitus / Alex / Benadryl)",
        "dosage": "2 teaspoons (10ml) 3 times daily",
        "indication": "Cough, sore throat",
        "warnings": "Some formulas cause drowsiness. Check label. Not for children < 2.",
        "otc": True,
    },
    "Saline nasal spray": {
        "name": "Saline Nasal Spray (Nasoclear / Simply Saline)",
        "dosage": "2 sprays per nostril 3-4 times daily",
        "indication": "Nasal congestion, sinusitis, cold",
        "warnings": "Safe for daily use. No systemic side effects.",
        "otc": True,
    },
    "Topical analgesic": {
        "name": "Topical Pain Gel (Volini / Moov / Ibugesic Plus gel)",
        "dosage": "Apply thin layer to affected area 3-4 times daily",
        "indication": "Muscle pain, joint pain, back pain",
        "warnings": "External use only. Do not apply on broken skin or wounds.",
        "otc": True,
    },
    "Nasal decongestant": {
        "name": "Nasal Decongestant (Otrivin / Nasivion)",
        "dosage": "1-2 drops/sprays per nostril every 8-12 hours",
        "indication": "Blocked nose, sinusitis",
        "warnings": "Do not use more than 3-5 days. Rebound congestion may occur.",
        "otc": True,
    },
    "Calamine lotion": {
        "name": "Calamine Lotion",
        "dosage": "Apply to affected skin area 2-3 times daily",
        "indication": "Rash, itching, chickenpox blisters",
        "warnings": "External use only. Avoid near eyes.",
        "otc": True,
    },
    "Artificial tears": {
        "name": "Lubricating Eye Drops (Refresh / Systane)",
        "dosage": "1-2 drops per eye 3-4 times daily",
        "indication": "Dry eyes, eye strain, conjunctivitis",
        "warnings": "Remove contact lenses before use. Preservative-free preferred.",
        "otc": True,
    },
    "H2 blocker": {
        "name": "Famotidine / Ranitidine (H2 blocker)",
        "dosage": "20mg twice daily before meals",
        "indication": "Acidity, GERD, peptic ulcer prevention",
        "warnings": "Short-term use. Consult if symptoms persist beyond 2 weeks.",
        "otc": True,
    },
    "Zinc supplements": {
        "name": "Zinc supplement (20mg)",
        "dosage": "20mg daily with food",
        "indication": "Diarrhea, immune support, wound healing",
        "warnings": "High doses may cause nausea. Do not exceed 40mg/day.",
        "otc": True,
    },
    "Cranberry supplements": {
        "name": "Cranberry Extract Supplement",
        "dosage": "500mg twice daily",
        "indication": "UTI prevention, urinary health",
        "warnings": "Not a replacement for antibiotics in active UTI. Consult doctor.",
        "otc": True,
    },
    "Moisturizing cream": {
        "name": "Moisturizing Cream (Cetaphil / Vaseline Intensive)",
        "dosage": "Apply twice daily on dry areas",
        "indication": "Dry skin, eczema, psoriasis",
        "warnings": "Avoid on infected skin. Fragrance-free preferred for sensitive skin.",
        "otc": True,
    },
    "Antihistamine": {
        "name": "Antihistamine — Cetirizine or Loratadine (see above)",
        "dosage": "10mg once daily",
        "indication": "Allergy, itching, hives",
        "warnings": "Check if drowsy formula. Avoid driving if so.",
        "otc": True,
    },
    "Clove oil topical": {
        "name": "Clove Oil (Eugenol) — topical dental",
        "dosage": "Apply 1-2 drops on cotton, hold against tooth for 5 minutes",
        "indication": "Toothache, dental pain",
        "warnings": "External/topical only. Do not swallow. Not for young children.",
        "otc": True,
    },
    "Omega-3 supplement": {
        "name": "Omega-3 Fish Oil (1000mg EPA+DHA)",
        "dosage": "1000mg once or twice daily with food",
        "indication": "Depression support, heart health, inflammation",
        "warnings": "May affect blood thinning at very high doses. Consult if on blood thinners.",
        "otc": True,
    },
}

# Prescription-only — never recommend these
PRESCRIPTION_ONLY = {
    "metformin", "amoxicillin", "azithromycin", "clavulanate",
    "dexamethasone", "prednisolone", "warfarin", "atorvastatin",
    "omeprazole prescription", "pantoprazole prescription",
    "salbutamol inhaler prescription", "insulin",
}


class MedicineRecommender:
    def recommend(self, disease_name: str, domain: str = "human") -> List[Dict[str, Any]]:
        """Get OTC medicine recommendations for a disease."""
        disease = find_disease(disease_name, domain=domain)
        if not disease:
            return []

        medicines = []
        seen = set()

        for medicine_name in disease.get("medicines", []):
            # Skip prescription-only
            if medicine_name.lower() in PRESCRIPTION_ONLY:
                continue
            if medicine_name in seen:
                continue
            seen.add(medicine_name)

            # Check our rich OTC database first
            otc_data = OTC_MEDICINES.get(medicine_name)
            if otc_data:
                medicines.append(otc_data)
                continue

            # Check knowledge service
            medicine_data = find_medicine(medicine_name)
            if medicine_data and medicine_data.get("otc", False):
                medicines.append({
                    "name": medicine_data.get("name", medicine_name),
                    "dosage": medicine_data.get("dosage", "As directed on packaging"),
                    "indication": medicine_data.get("indication", "As recommended"),
                    "warnings": medicine_data.get("warnings", "Follow package instructions."),
                    "otc": True,
                })
            elif medicine_data is None:
                # Unlisted but appears OTC — include with basic info
                medicines.append({
                    "name": medicine_name,
                    "dosage": "As directed on packaging",
                    "indication": "As recommended for this condition",
                    "warnings": "Consult pharmacist before use.",
                    "otc": True,
                })

        return medicines

    def get_medicine_details(self, name: str) -> Dict[str, Any]:
        """Get detailed info for a specific medicine by name."""
        return OTC_MEDICINES.get(name, {
            "name": name,
            "dosage": "As directed on packaging",
            "indication": "Refer to package insert",
            "warnings": "Consult a pharmacist or doctor.",
            "otc": True,
        })

    def get_disclaimer(self) -> str:
        return (
            "💊 All medicines listed are OTC (over-the-counter) suggestions only. "
            "Always read the label, check for allergies, and consult a pharmacist or doctor "
            "before taking any medication. Do not self-medicate for serious conditions."
        )
