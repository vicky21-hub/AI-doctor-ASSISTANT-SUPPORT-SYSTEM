"""
report_analyzer_service.py — Bridge between OCR output and AI Doctor Engine.

Responsibilities:
  1. Detect abnormal laboratory parameters (reuses OCR LAB_RANGES + CONDITION_RULES)
  2. Generate structured clinical findings from lab values
  3. Calculate an educational risk level (low / medium / high)
  4. Suggest follow-up laboratory tests when appropriate
  5. Convert findings into symptoms and call HumanHealthEngine.assess()
  6. Merge OCR analysis + AI assessment into one unified response

Does NOT:
  - Duplicate OCR logic  (calls ocr_service internals via passed-in ocr_result)
  - Duplicate disease prediction (delegates to HumanHealthEngine)
  - Maintain its own knowledge base
  - Create a new AI engine
"""

import logging
from typing import Any, Dict, List

from ai.human_health_engine import HumanHealthEngine
from services.ocr_service import LAB_RANGES, CONDITION_RULES

logger = logging.getLogger(__name__)

# ── Singleton engine — reuse the same instance across requests ─────────────────
_engine = HumanHealthEngine()

# ── Condition name → symptom keywords understood by HumanHealthEngine ──────────
_CONDITION_TO_SYMPTOMS: Dict[str, List[str]] = {
    "iron deficiency anemia":               ["fatigue", "weakness", "anemia", "pale skin", "shortness of breath"],
    "diabetes / pre-diabetes":              ["increased thirst", "frequent urination", "fatigue", "blurred vision", "diabetes"],
    "elevated cholesterol (dyslipidemia)":  ["cholesterol", "chest pain", "fatigue", "hypertension"],
    "kidney dysfunction":                   ["fatigue", "swelling", "decreased urination", "kidney pain"],
    "liver dysfunction":                    ["fatigue", "jaundice", "abdominal pain", "nausea", "liver"],
    "hypothyroidism":                       ["fatigue", "weight gain", "cold intolerance", "thyroid", "depression"],
    "vitamin d deficiency":                 ["fatigue", "bone pain", "muscle weakness", "vitamin d deficiency"],
    "thrombocytopenia (low platelets)":     ["easy bruising", "bleeding", "fatigue", "platelets low"],
    "leukocytosis (high wbc — possible infection)": ["fever", "infection", "fatigue", "body pain"],
    "hypertension":                         ["headache", "dizziness", "chest pain", "hypertension"],
}

# ── Follow-up test suggestions per abnormal parameter ─────────────────────────
_FOLLOWUP_TESTS: Dict[str, List[str]] = {
    "hemoglobin":    ["Serum Ferritin", "Serum Iron", "TIBC", "Peripheral Blood Smear"],
    "wbc":           ["Differential WBC Count", "CRP", "ESR", "Blood Culture"],
    "platelets":     ["Peripheral Blood Smear", "Dengue NS1 Antigen", "Bone Marrow Biopsy (if severe)"],
    "glucose":       ["HbA1c", "Fasting Insulin", "OGTT", "Urine Microalbumin"],
    "hba1c":         ["Fasting Blood Glucose", "Post-Prandial Glucose", "Urine Microalbumin"],
    "creatinine":    ["eGFR", "Urine Routine", "Urine Microalbumin", "Renal Ultrasound"],
    "urea":          ["Serum Creatinine", "eGFR", "Urine Routine"],
    "cholesterol":   ["LDL", "HDL", "Triglycerides", "Apolipoprotein B"],
    "ldl":           ["Total Cholesterol", "HDL", "Triglycerides", "Lp(a)"],
    "triglycerides": ["Fasting Lipid Profile", "Blood Glucose", "Thyroid Function"],
    "sgot":          ["SGPT", "Alkaline Phosphatase", "Bilirubin", "Hepatitis B & C Serology"],
    "sgpt":          ["SGOT", "Alkaline Phosphatase", "Bilirubin", "Hepatitis B & C Serology"],
    "bilirubin":     ["Direct Bilirubin", "Indirect Bilirubin", "LFT Complete", "Abdominal Ultrasound"],
    "tsh":           ["Free T3", "Free T4", "Anti-TPO Antibodies"],
    "vitamin_d":     ["Parathyroid Hormone (PTH)", "Serum Calcium", "Serum Phosphorus"],
    "vitamin_b12":   ["Folate", "Homocysteine", "Peripheral Blood Smear"],
    "systolic_bp":   ["ECG", "Echocardiogram", "Renal Function Tests", "Urine Microalbumin"],
    "diastolic_bp":  ["ECG", "Echocardiogram", "Renal Function Tests"],
}

# ── Risk level weights ─────────────────────────────────────────────────────────
_RISK_WEIGHTS = {"high": 3, "medium": 2, "low": 1}


def _calculate_risk_level(
    detected_conditions: List[Dict[str, Any]],
    critical_alerts: List[Dict[str, str]],
    abnormal_count: int,
) -> str:
    """
    Educational risk level based on:
    - Presence of critical alerts (always HIGH)
    - Weighted sum of detected condition risks
    - Number of abnormal parameters
    """
    if critical_alerts:
        return "high"

    if not detected_conditions and abnormal_count == 0:
        return "low"

    score = sum(_RISK_WEIGHTS.get(c.get("risk", "low"), 1) for c in detected_conditions)
    score += abnormal_count  # each abnormal param adds 1

    if score >= 5:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _build_clinical_findings(
    lab_values: Dict[str, float],
    abnormal_values: List[Dict[str, Any]],
    detected_conditions: List[Dict[str, Any]],
    critical_alerts: List[Dict[str, str]],
    report_type: str,
) -> List[str]:
    """
    Generate structured, human-readable clinical finding sentences.
    Each finding is one clear statement a patient can understand.
    """
    findings: List[str] = []

    # Critical alerts first
    for alert in critical_alerts:
        findings.append(f"⚠️ CRITICAL: {alert['message']}")

    # Abnormal parameter findings
    for ab in abnormal_values:
        direction = "elevated above" if ab["status"] == "high" else "below"
        findings.append(
            f"{ab['parameter']} is {direction} the normal range "
            f"({ab['value']} {ab['unit']}; reference: {ab['reference']})."
        )

    # Condition-level findings
    for cond in detected_conditions:
        findings.append(
            f"{cond['condition']} indicators detected ({cond['severity']} severity). "
            f"{cond['advice']}"
        )

    if not findings:
        if lab_values:
            findings.append(
                f"All {len(lab_values)} extracted lab parameters are within normal reference ranges."
            )
        else:
            findings.append(
                f"Report processed as {report_type}. "
                "No specific abnormal values could be extracted from the text."
            )

    return findings


def _derive_symptoms(detected_conditions: List[Dict[str, Any]]) -> List[str]:
    """
    Convert detected OCR conditions into symptom keywords that
    HumanHealthEngine.assess() understands.
    Deduplicates while preserving order.
    """
    seen: set = set()
    symptoms: List[str] = []
    for cond in detected_conditions:
        key = cond.get("condition", "").lower()
        for condition_key, syms in _CONDITION_TO_SYMPTOMS.items():
            if condition_key in key or key in condition_key:
                for s in syms:
                    if s not in seen:
                        seen.add(s)
                        symptoms.append(s)
                break
    return symptoms or ["fatigue", "general discomfort"]


def _suggest_followup_tests(
    abnormal_values: List[Dict[str, Any]],
    existing_tests: List[str],
) -> List[str]:
    """
    Suggest follow-up tests for each abnormal parameter.
    Skips tests already present in the report (existing_tests).
    Returns deduplicated list, max 8 suggestions.
    """
    existing_lower = {t.lower() for t in existing_tests}
    seen: set = set()
    suggestions: List[str] = []

    for ab in abnormal_values:
        param_key = ab.get("parameter", "").lower().replace(" ", "_")
        for test in _FOLLOWUP_TESTS.get(param_key, []):
            if test.lower() not in existing_lower and test not in seen:
                seen.add(test)
                suggestions.append(test)

    return suggestions[:8]


def enrich(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point.

    Takes the raw dict returned by OCRService.process_file() and returns
    a unified response that merges OCR findings with AI Doctor assessment.

    Steps:
      1. Extract structured data from ocr_result (no re-OCR)
      2. Detect abnormal parameters (reuses OCR LAB_RANGES already applied)
      3. Generate clinical findings
      4. Calculate educational risk level
      5. Suggest follow-up tests
      6. Derive symptoms → call HumanHealthEngine.assess()
      7. Merge everything into one response
    """
    # ── Guard: if OCR itself failed, return as-is ──────────────────────────────
    if not ocr_result.get("success"):
        return ocr_result

    lab_values         = ocr_result.get("lab_values", {})
    abnormal_values    = ocr_result.get("abnormal_values", [])
    detected_conditions = ocr_result.get("detected_conditions", [])
    critical_alerts    = ocr_result.get("critical_alerts", [])
    report_type        = ocr_result.get("report_type", "general report")
    existing_tests     = ocr_result.get("recommended_tests", [])

    # ── Step 3: Structured clinical findings ──────────────────────────────────
    clinical_findings = _build_clinical_findings(
        lab_values, abnormal_values, detected_conditions,
        critical_alerts, report_type,
    )

    # ── Step 4: Educational risk level ────────────────────────────────────────
    risk_level = _calculate_risk_level(
        detected_conditions, critical_alerts, len(abnormal_values)
    )

    # ── Step 5: Follow-up test suggestions ────────────────────────────────────
    followup_tests = _suggest_followup_tests(abnormal_values, existing_tests)

    # ── Step 6: Derive symptoms → HumanHealthEngine ───────────────────────────
    symptoms = _derive_symptoms(detected_conditions)
    ai_assessment: Dict[str, Any] = {}
    try:
        ai_assessment = _engine.assess(
            text=" ".join(symptoms),
            symptoms=symptoms,
            severity="moderate" if risk_level == "medium" else risk_level,
            history=f"Lab report: {report_type}. Findings: {', '.join(clinical_findings[:3])}",
        )
        logger.info(
            "[ReportAnalyzer] AI assessment: disease=%s confidence=%s",
            ai_assessment.get("disease"), ai_assessment.get("confidence"),
        )
    except Exception as exc:
        logger.error("[ReportAnalyzer] HumanHealthEngine.assess() failed: %s", exc)

    # ── Step 7: Merge into unified response ───────────────────────────────────
    # OCR fields take precedence for lab-specific data.
    # AI fields fill in clinical narrative, medicines, diet, specialist.
    unified = {
        # ── Identity ──────────────────────────────────────────────────────────
        "success":      True,
        "source":       "report_upload",
        "report_type":  report_type,

        # ── Primary condition ─────────────────────────────────────────────────
        # Prefer AI disease name if confident, else use OCR primary condition
        "disease":    (
            ai_assessment.get("disease")
            if ai_assessment.get("confidence", 0) >= 40
            else ocr_result.get("disease", "General Health Report")
        ),
        "condition":  (
            ai_assessment.get("disease")
            if ai_assessment.get("confidence", 0) >= 40
            else ocr_result.get("condition", "General Health Report")
        ),
        "confidence": max(
            ocr_result.get("confidence", 0),
            ai_assessment.get("confidence", 0),
        ),

        # ── Risk ──────────────────────────────────────────────────────────────
        "risk_level":   risk_level,
        "overall_risk": risk_level,
        "risk":         risk_level,
        "emergency":    bool(critical_alerts) or ai_assessment.get("emergency", False),

        # ── OCR lab data (unchanged from OCR service) ─────────────────────────
        "lab_values":          lab_values,
        "abnormal_values":     abnormal_values,
        "detected_conditions": detected_conditions,
        "critical_alerts":     critical_alerts,
        "extracted_text":      ocr_result.get("extracted_text", ""),
        "ocr_confidence":      ocr_result.get("ocr_confidence", 0.0),
        "image_quality":       ocr_result.get("image_quality", "unknown"),

        # ── New structured fields ─────────────────────────────────────────────
        "clinical_findings":   clinical_findings,
        "followup_tests":      followup_tests,

        # ── AI narrative fields (from HumanHealthEngine) ──────────────────────
        "description":         ai_assessment.get("description", ""),
        "causes":              ai_assessment.get("causes", []),
        "medicines":           ai_assessment.get("medicines", []),
        "medicine_details":    ai_assessment.get("medicine_details", []),
        "diet":                ai_assessment.get("diet", []),
        "home_remedies":       ai_assessment.get("home_remedies", []),
        "precautions":         ai_assessment.get("precautions", [])
                               or [c["advice"] for c in detected_conditions],
        "recommended_tests":   list(dict.fromkeys(
            ai_assessment.get("recommended_tests", []) + followup_tests
        ))[:8],
        "doctor_type":         (
            ocr_result.get("recommended_specialist")
            or ai_assessment.get("doctor_type", "General Physician")
        ),
        "emergency_warnings":  ai_assessment.get("emergency_warnings", []),
        "related_conditions":  ai_assessment.get("related_conditions", []),

        # ── Summary ───────────────────────────────────────────────────────────
        "summary": ocr_result.get("summary", ""),

        # ── Recommendations: merge OCR advice + AI recommendations ────────────
        "recommendations": list(dict.fromkeys(
            [c["advice"] for c in detected_conditions]
            + ai_assessment.get("recommendations", [])
        ))[:6] or ["Consult a qualified healthcare provider for full interpretation."],

        # ── Keywords for history search ───────────────────────────────────────
        "keywords": ocr_result.get("keywords", []),
    }

    return unified
