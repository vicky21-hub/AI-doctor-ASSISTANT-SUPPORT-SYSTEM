"""
ocr_service.py — Professional OCR pipeline with image preprocessing and
structured medical report analysis.

OCR dependency chain:
  pytesseract (Python wrapper)  →  Tesseract binary (must be installed separately)

If Tesseract binary is missing, pytesseract.image_to_string raises
  pytesseract.TesseractNotFoundError
which is caught here and reported with a clear diagnostic message.
"""

import re
import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Optional heavy deps — graceful degradation ────────────────────────────────
try:
    import pytesseract
    from PIL import Image, ImageFilter, ImageEnhance
    PYTESSERACT_INSTALLED = True
except ImportError:
    PYTESSERACT_INSTALLED = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# ── Tesseract binary detection ────────────────────────────────────────────────

def _detect_tesseract() -> Dict[str, Any]:
    """
    Check whether the Tesseract OCR binary is installed and accessible.
    Returns a dict with keys: available (bool), version (str), path (str), error (str).
    """
    result = {"available": False, "version": "", "path": "", "error": ""}

    # 1. Check PATH using shutil.which
    tess_path = shutil.which("tesseract")

    # 2. Common Windows install locations if not on PATH
    if not tess_path and os.name == "nt":
        windows_candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tesseract-OCR", "tesseract.exe"),
            os.path.join(os.environ.get("APPDATA", ""), "Tesseract-OCR", "tesseract.exe"),
        ]
        for candidate in windows_candidates:
            if candidate and os.path.isfile(candidate):
                tess_path = candidate
                break

    if not tess_path:
        result["error"] = (
            "Tesseract OCR engine is not installed or not found on PATH. "
            "Install from: https://github.com/UB-Mannheim/tesseract/wiki (Windows) "
            "or 'sudo apt install tesseract-ocr' (Linux/Ubuntu)."
        )
        return result

    result["path"] = tess_path

    # Tell pytesseract where to find it if not on PATH
    if PYTESSERACT_INSTALLED:
        pytesseract.pytesseract.tesseract_cmd = tess_path

    # 3. Run tesseract --version to confirm it works
    try:
        proc = subprocess.run(
            [tess_path, "--version"],
            capture_output=True, text=True, timeout=5
        )
        version_output = proc.stdout or proc.stderr
        # First line is e.g. "tesseract 5.3.1"
        first_line = version_output.strip().split("\n")[0] if version_output else ""
        result["version"] = first_line
        result["available"] = True
    except Exception as e:
        result["error"] = f"Tesseract found at {tess_path} but failed to run: {e}"

    return result


# Run detection once at module load — used by OCRService and health endpoint
TESSERACT_STATUS = _detect_tesseract()
OCR_AVAILABLE = PYTESSERACT_INSTALLED and TESSERACT_STATUS["available"]

# Log status at startup
if OCR_AVAILABLE:
    logger.info("OCR Engine: AVAILABLE — %s at %s",
                TESSERACT_STATUS["version"], TESSERACT_STATUS["path"])
else:
    if not PYTESSERACT_INSTALLED:
        logger.warning("OCR Engine: NOT READY — pytesseract Python package not installed.")
    else:
        logger.warning("OCR Engine: NOT READY — %s", TESSERACT_STATUS["error"])


# ── Lab reference ranges ───────────────────────────────────────────────────────
LAB_RANGES = {
    # CBC
    "hemoglobin":    {"male": (13.5, 17.5), "female": (12.0, 15.5), "unit": "g/dL",  "key": ["hb", "hemoglobin", "haemoglobin", "hgb"]},
    "rbc":           {"male": (4.5, 5.9),   "female": (4.1, 5.1),   "unit": "M/µL",  "key": ["rbc", "red blood cell", "erythrocyte"]},
    "wbc":           {"both": (4.0, 11.0),                           "unit": "K/µL",  "key": ["wbc", "white blood cell", "leukocyte", "tlc"]},
    "platelets":     {"both": (150, 400),                            "unit": "K/µL",  "key": ["platelet", "plt", "thrombocyte"]},
    "hematocrit":    {"male": (41, 53),     "female": (36, 46),      "unit": "%",     "key": ["hematocrit", "hct", "pcv"]},
    # Metabolic
    "glucose":       {"both": (70, 100),                             "unit": "mg/dL", "key": ["glucose", "blood sugar", "fbs", "rbs", "fasting sugar"]},
    "hba1c":         {"both": (4.0, 5.6),                            "unit": "%",     "key": ["hba1c", "glycated hemoglobin", "a1c"]},
    "creatinine":    {"male": (0.7, 1.3),   "female": (0.5, 1.1),   "unit": "mg/dL", "key": ["creatinine", "serum creatinine"]},
    "urea":          {"both": (7, 20),                               "unit": "mg/dL", "key": ["urea", "bun", "blood urea nitrogen"]},
    # Lipids
    "cholesterol":   {"both": (0, 200),                              "unit": "mg/dL", "key": ["total cholesterol", "cholesterol"]},
    "ldl":           {"both": (0, 100),                              "unit": "mg/dL", "key": ["ldl", "low density lipoprotein"]},
    "hdl":           {"male": (40, 999),    "female": (50, 999),     "unit": "mg/dL", "key": ["hdl", "high density lipoprotein"]},
    "triglycerides": {"both": (0, 150),                              "unit": "mg/dL", "key": ["triglyceride", "tg", "trigs"]},
    # Liver
    "sgot":          {"both": (10, 40),                              "unit": "U/L",   "key": ["sgot", "ast", "aspartate aminotransferase"]},
    "sgpt":          {"both": (7, 56),                               "unit": "U/L",   "key": ["sgpt", "alt", "alanine aminotransferase"]},
    "bilirubin":     {"both": (0.2, 1.2),                            "unit": "mg/dL", "key": ["bilirubin", "total bilirubin"]},
    # Thyroid
    "tsh":           {"both": (0.4, 4.0),                            "unit": "mIU/L", "key": ["tsh", "thyroid stimulating hormone"]},
    # Vitamins
    "vitamin_d":     {"both": (30, 100),                             "unit": "ng/mL", "key": ["vitamin d", "25-oh vitamin d", "25 oh d"]},
    "vitamin_b12":   {"both": (200, 900),                            "unit": "pg/mL", "key": ["vitamin b12", "b12", "cobalamin"]},
    # Blood pressure (parsed separately)
    "systolic_bp":   {"both": (90, 120),                             "unit": "mmHg",  "key": ["systolic", "sbp"]},
    "diastolic_bp":  {"both": (60, 80),                              "unit": "mmHg",  "key": ["diastolic", "dbp"]},
}

# ── Condition detection rules from lab values ──────────────────────────────────
CONDITION_RULES = [
    {
        "condition": "Iron Deficiency Anemia",
        "check": lambda v: v.get("hemoglobin") is not None and v["hemoglobin"] < 12.0,
        "severity": lambda v: "severe" if v.get("hemoglobin", 99) < 8 else "mild to moderate",
        "risk": "medium",
        "advice": "Low hemoglobin detected. Iron supplementation and dietary changes recommended.",
    },
    {
        "condition": "Diabetes / Pre-diabetes",
        "check": lambda v: (v.get("glucose") is not None and v["glucose"] > 126) or
                           (v.get("hba1c") is not None and v["hba1c"] > 6.5),
        "severity": lambda v: "Type 2 Diabetes" if (v.get("glucose", 0) > 200 or v.get("hba1c", 0) > 8) else "Pre-diabetes / Early Diabetes",
        "risk": "high",
        "advice": "Elevated blood sugar detected. Consult an endocrinologist.",
    },
    {
        "condition": "Elevated Cholesterol (Dyslipidemia)",
        "check": lambda v: (v.get("cholesterol") is not None and v["cholesterol"] > 200) or
                           (v.get("ldl") is not None and v["ldl"] > 130),
        "severity": lambda v: "high" if v.get("cholesterol", 0) > 240 else "borderline",
        "risk": "medium",
        "advice": "High cholesterol detected. Dietary changes and cardiology review recommended.",
    },
    {
        "condition": "Kidney Dysfunction",
        "check": lambda v: (v.get("creatinine") is not None and v["creatinine"] > 1.4) or
                           (v.get("urea") is not None and v["urea"] > 25),
        "severity": lambda v: "significant" if v.get("creatinine", 0) > 2.0 else "mild",
        "risk": "high",
        "advice": "Elevated kidney markers. Nephrology consultation recommended.",
    },
    {
        "condition": "Liver Dysfunction",
        "check": lambda v: (v.get("sgot") is not None and v["sgot"] > 45) or
                           (v.get("sgpt") is not None and v["sgpt"] > 60),
        "severity": lambda v: "significant" if max(v.get("sgot", 0), v.get("sgpt", 0)) > 100 else "mild",
        "risk": "medium",
        "advice": "Elevated liver enzymes. Gastroenterology review recommended.",
    },
    {
        "condition": "Hypothyroidism",
        "check": lambda v: v.get("tsh") is not None and v["tsh"] > 4.5,
        "severity": lambda v: "subclinical" if v.get("tsh", 0) < 10 else "overt",
        "risk": "medium",
        "advice": "High TSH detected. Thyroid function evaluation recommended.",
    },
    {
        "condition": "Vitamin D Deficiency",
        "check": lambda v: v.get("vitamin_d") is not None and v["vitamin_d"] < 20,
        "severity": lambda v: "severe" if v.get("vitamin_d", 99) < 10 else "moderate",
        "risk": "low",
        "advice": "Low Vitamin D. Supplementation and sun exposure recommended.",
    },
    {
        "condition": "Thrombocytopenia (Low Platelets)",
        "check": lambda v: v.get("platelets") is not None and v["platelets"] < 150,
        "severity": lambda v: "severe" if v.get("platelets", 999) < 50 else "mild",
        "risk": "high",
        "advice": "Low platelet count. Hematology evaluation required.",
    },
    {
        "condition": "Leukocytosis (High WBC — Possible Infection)",
        "check": lambda v: v.get("wbc") is not None and v["wbc"] > 11.0,
        "severity": lambda v: "significant" if v.get("wbc", 0) > 20 else "mild",
        "risk": "medium",
        "advice": "Elevated white blood cells suggest possible infection or inflammation.",
    },
    {
        "condition": "Hypertension",
        "check": lambda v: (v.get("systolic_bp") is not None and v["systolic_bp"] > 130) or
                           (v.get("diastolic_bp") is not None and v["diastolic_bp"] > 85),
        "severity": lambda v: "Stage 2" if v.get("systolic_bp", 0) > 160 else "Stage 1",
        "risk": "high",
        "advice": "Elevated blood pressure detected. Cardiology review recommended.",
    },
]


class OCRService:
    def __init__(self):
        # Internal state — reset per file processed
        self._last_ocr_confidence: float = 0.0
        self._last_image_quality: str    = "unknown"

    # ── Image preprocessing ────────────────────────────────────────────────────

    def _deskew(self, gray: Any) -> Any:
        """Deskew a grayscale image using Hough-based angle detection with downsampled search."""
        if not CV2_AVAILABLE:
            return gray
        try:
            h, w = gray.shape[:2]
            if max(h, w) > 800:
                scale = 800.0 / max(h, w)
                small = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            else:
                small = gray
            edges = cv2.Canny(small, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=80, maxLineGap=10)
            if lines is None:
                return gray
            angles = []
            for line in lines[:30]:
                x1, y1, x2, y2 = line[0]
                if x2 != x1:
                    angles.append(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if not angles:
                return gray
            median_angle = float(np.median(angles))
            if abs(median_angle) < 0.5 or abs(median_angle) > 45.0:
                return gray
            M = cv2.getRotationMatrix2D((w / 2, h / 2), median_angle, 1.0)
            return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        except Exception:
            return gray

    def _preprocess_with_cv2(self, image_path: str) -> Optional[Any]:
        """
        Fast, memory-bounded OpenCV preprocessing pipeline:
          1. Clamp image dimensions (max 1600px)
          2. Grayscale conversion
          3. Fast Gaussian noise reduction (1ms vs 30s NLM)
          4. Deskew angle correction
          5. Adaptive Gaussian thresholding
        """
        if not CV2_AVAILABLE:
            return None
        try:
            img = cv2.imread(image_path)
            if img is None:
                logger.warning("[OCR] cv2.imread returned None for %s", image_path)
                return None
            h, w = img.shape[:2]
            max_dim = max(h, w)
            if max_dim > 1600:
                scale = 1600.0 / max_dim
                img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            elif max_dim < 800 and w > 0:
                scale = 1000.0 / max_dim
                img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            deskewed = self._deskew(blurred)
            thresh = cv2.adaptiveThreshold(
                deskewed, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            return thresh
        except Exception as exc:
            logger.warning("[OCR] cv2 preprocessing failed for %s: %s", image_path, exc)
            return None

    def _preprocess_with_pil(self, image_path: str) -> Optional[Any]:
        """
        PIL-based preprocessing fallback (used when OpenCV is unavailable).
        Order: open → grayscale → upscale → contrast enhance.
        Sharpness enhancement removed: PIL sharpening on already-enhanced
        contrast images tends to over-sharpen and introduce ringing artefacts.
        """
        if not PYTESSERACT_INSTALLED:
            return None
        try:
            img = Image.open(image_path).convert("L")
            # Upscale first so contrast enhancement works on more pixels
            if img.width < 1000:
                ratio = 1000 / img.width
                img = img.resize((1000, int(img.height * ratio)), Image.LANCZOS)
            # Moderate contrast boost — 1.5 is enough; 2.0 clips fine detail
            img = ImageEnhance.Contrast(img).enhance(1.5)
            return img
        except Exception as exc:
            logger.warning("[OCR] PIL preprocessing failed for %s: %s", image_path, exc)
            return None

    # ── PATCH: OCR confidence score ────────────────────────────────────────────

    def _calc_ocr_confidence(self, pil_img: Any) -> float:
        """Calculate average OCR word confidence using pytesseract.image_to_data."""
        if not (PYTESSERACT_INSTALLED and TESSERACT_STATUS["available"]):
            return 0.0
        try:
            ocr_data = pytesseract.image_to_data(
                pil_img, output_type=pytesseract.Output.DICT
            )
            confidences = [
                int(c) for c in ocr_data["conf"] if str(c) != "-1" and int(c) >= 0
            ]
            return round(sum(confidences) / len(confidences), 1) if confidences else 0.0
        except Exception:
            return 0.0

    # ── PATCH: Image quality detection ────────────────────────────────────────

    def detect_image_quality(self, image_path: str) -> str:
        """Return image quality: 'excellent', 'good', or 'blurry'."""
        return self._detect_image_quality(image_path)

    def _detect_image_quality(self, image_path: str) -> str:
        """Internal: use Laplacian variance to measure sharpness."""
        if not CV2_AVAILABLE:
            return "unknown"
        try:
            img = cv2.imread(image_path)
            if img is None:
                return "unknown"
            gray      = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            variance  = cv2.Laplacian(gray, cv2.CV_64F).var()
            if variance >= 300:
                return "excellent"
            elif variance >= 100:
                return "good"
            else:
                return "blurry"
        except Exception:
            return "unknown"

    # ── PATCH: OCR text normalization ────────────────────────────────────────

    def normalize_ocr_text(self, text: str) -> str:
        """Fix common OCR character substitution errors in medical reports."""
        _OCR_FIXES = [
            (r"Hemoqlobin",  "Hemoglobin"),
            (r"Haemoqlobin", "Haemoglobin"),
            (r"Glocose",     "Glucose"),
            (r"Glucos[e3]",  "Glucose"),
            (r"Plateiet",    "Platelet"),
            (r"Platelct",    "Platelet"),
            (r"Creatinlne",  "Creatinine"),
            (r"Creatln[li]ne", "Creatinine"),
            (r"Triqlyceride", "Triglyceride"),
            (r"Cholestcrol", "Cholesterol"),
            (r"Bi1irubin",   "Bilirubin"),
            (r"B1lirubin",   "Bilirubin"),
            (r"Haematocrit", "Hematocrit"),
            (r"HaematocFit", "Hematocrit"),
            (r"Leukocyte",   "Leukocyte"),
            (r"Erthrocyte",  "Erythrocyte"),
            (r"Thyrold",     "Thyroid"),
            (r"Thyr0id",     "Thyroid"),
            (r"\bl\b(?=\s*\d)", "1"),  # lone 'l' before number -> '1'
            (r"\bO\b(?=\s*\d)", "0"),  # lone 'O' before number -> '0'
        ]
        try:
            for pattern, replacement in _OCR_FIXES:
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        except Exception:
            pass
        return text

    # ── PATCH: Report type detection ─────────────────────────────────────────

    def detect_report_type(self, text: str) -> str:
        """Detect the medical report type from extracted text."""
        tl = text.lower()
        _REPORT_SIGNATURES = [
            ("cbc",              ["cbc", "complete blood count", "hemoglobin", "wbc", "platelets", "rbc", "hematocrit"]),
            ("lipid profile",    ["lipid profile", "cholesterol", "ldl", "hdl", "triglyceride", "vldl"]),
            ("thyroid profile",  ["thyroid", "tsh", "t3", "t4", "free t4", "free t3", "thyroid stimulating"]),
            ("liver function",   ["liver function", "sgot", "sgpt", "ast", "alt", "bilirubin", "alkaline phosphatase", "albumin"]),
            ("kidney function",  ["kidney function", "creatinine", "urea", "bun", "gfr", "uric acid", "electrolytes"]),
            ("diabetes report",  ["hba1c", "glycated hemoglobin", "fasting glucose", "ppbs", "ogtt", "fbs", "diabetes"]),
        ]
        try:
            for report_type, keywords in _REPORT_SIGNATURES:
                hits = sum(1 for kw in keywords if kw in tl)
                if hits >= 2:
                    return report_type
        except Exception:
            pass
        return "general report"

    # ── PATCH: Critical value detection ──────────────────────────────────────

    def detect_critical_values(self, lab_values: Dict[str, float]) -> List[Dict[str, str]]:
        """Detect life-threatening lab values and return critical alerts."""
        CRITICAL_VALUES = [
            {
                "param":   "hemoglobin",
                "check":   lambda v: v < 7.0,
                "alert":   "Critical Anemia",
                "message": "Hemoglobin critically low (< 7.0 g/dL). Urgent evaluation required.",
                "action":  "Seek immediate medical attention. Possible need for transfusion.",
            },
            {
                "param":   "glucose",
                "check":   lambda v: v > 400,
                "alert":   "Critical Hyperglycemia",
                "message": "Blood glucose critically high (> 400 mg/dL). Risk of diabetic ketoacidosis.",
                "action":  "Emergency endocrinology consult required immediately.",
            },
            {
                "param":   "glucose",
                "check":   lambda v: v < 50,
                "alert":   "Severe Hypoglycemia",
                "message": "Blood glucose critically low (< 50 mg/dL). Risk of hypoglycemic coma.",
                "action":  "Administer glucose immediately. Emergency care if unconscious.",
            },
            {
                "param":   "platelets",
                "check":   lambda v: v < 50,
                "alert":   "Severe Thrombocytopenia",
                "message": "Platelet count critically low (< 50 K/uL). Bleeding risk is high.",
                "action":  "Urgent hematology consultation required.",
            },
            {
                "param":   "creatinine",
                "check":   lambda v: v > 5.0,
                "alert":   "Kidney Failure Risk",
                "message": "Creatinine critically elevated (> 5.0 mg/dL). Severe kidney impairment.",
                "action":  "Emergency nephrology evaluation. Dialysis may be required.",
            },
            {
                "param":   "systolic_bp",
                "check":   lambda v: v >= 180,
                "alert":   "Hypertensive Crisis",
                "message": "Systolic BP critically high (>= 180 mmHg). Hypertensive crisis.",
                "action":  "Immediate cardiology/emergency evaluation required.",
            },
        ]
        alerts = []
        try:
            for rule in CRITICAL_VALUES:
                val = lab_values.get(rule["param"])
                if val is not None and rule["check"](val):
                    alerts.append({
                        "alert":   rule["alert"],
                        "message": rule["message"],
                        "action":  rule["action"],
                    })
        except Exception:
            pass
        return alerts

    # ── PATCH: Specialist recommendation ────────────────────────────────────

    def recommend_specialist(self, conditions: List[Dict[str, Any]]) -> str:
        """Return the most relevant specialist based on detected conditions."""
        SPECIALIST_MAP = {
            "diabetes":        "Endocrinologist",
            "pre-diabetes":    "Endocrinologist",
            "thyroid":         "Endocrinologist",
            "hypothyroidism":  "Endocrinologist",
            "cholesterol":     "Cardiologist",
            "dyslipidemia":    "Cardiologist",
            "hypertension":    "Cardiologist",
            "kidney":          "Nephrologist",
            "creatinine":      "Nephrologist",
            "liver":           "Gastroenterologist",
            "bilirubin":       "Gastroenterologist",
            "hepatitis":       "Gastroenterologist",
            "anemia":          "Hematologist",
            "thrombocytopenia": "Hematologist",
            "leukocytosis":    "Hematologist",
            "vitamin d":       "General Physician",
            "vitamin b12":     "General Physician",
        }
        try:
            for cond in conditions:
                name = cond.get("condition", "").lower()
                for keyword, specialist in SPECIALIST_MAP.items():
                    if keyword in name:
                        return specialist
        except Exception:
            pass
        return "General Physician"

    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text using best available preprocessing.
        Returns extracted text, or raises RuntimeError with a clear message
        if Tesseract is not installed.
        """
        if not PYTESSERACT_INSTALLED:
            raise RuntimeError(
                "pytesseract Python package is not installed. "
                "Run: pip install pytesseract"
            )
        if not TESSERACT_STATUS["available"]:
            raise RuntimeError(TESSERACT_STATUS["error"])

        try:
            pil_img = None

            # ── CV2 pipeline (preferred) ───────────────────────────────────────
            if CV2_AVAILABLE:
                processed = self._preprocess_with_cv2(image_path)
                if processed is not None:
                    from PIL import Image as PILImage
                    pil_img = PILImage.fromarray(processed)

                    # Fast single-pass OCR with PSM 6
                    text_psm6 = pytesseract.image_to_string(
                        pil_img, config="--psm 6 --oem 3"
                    )

                    # Only fallback to PSM 3 if PSM 6 yielded very little text
                    if len(text_psm6.strip()) < 25:
                        text_psm3 = pytesseract.image_to_string(
                            pil_img, config="--psm 3 --oem 3"
                        )
                        if len(text_psm3.strip()) > len(text_psm6.strip()):
                            text_psm6 = text_psm3

                    if text_psm6.strip():
                        clean_len = len(text_psm6.strip())
                        self._last_ocr_confidence = min(92.0, max(60.0, 50.0 + min(clean_len, 500) * 0.08))
                        self._last_image_quality  = self._detect_image_quality(image_path)
                        logger.info(
                            "[OCR] CV2 pipeline succeeded — len=%d quality=%s",
                            clean_len, self._last_image_quality,
                        )
                        return text_psm6.strip()

            # ── PIL fallback ───────────────────────────────────────────────────
            processed_pil = self._preprocess_with_pil(image_path)
            if processed_pil:
                pil_img = processed_pil
                text = pytesseract.image_to_string(pil_img, config="--psm 6 --oem 3")
                self._last_ocr_confidence = self._calc_ocr_confidence(pil_img)
                self._last_image_quality  = self._detect_image_quality(image_path)
                logger.info(
                    "[OCR] PIL fallback succeeded — confidence=%.1f",
                    self._last_ocr_confidence,
                )
                return text.strip()

            # ── Raw fallback (no preprocessing) ───────────────────────────────
            logger.warning("[OCR] All preprocessing failed — attempting raw OCR on %s", image_path)
            pil_img = Image.open(image_path)
            text = pytesseract.image_to_string(pil_img, config="--psm 6 --oem 3").strip()
            self._last_ocr_confidence = self._calc_ocr_confidence(pil_img)
            self._last_image_quality  = self._detect_image_quality(image_path)
            return text

        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                "Tesseract OCR engine is not installed or not configured correctly. "
                "Install from: https://github.com/UB-Mannheim/tesseract/wiki"
            )
        except Exception as e:
            logger.error("[OCR] Extraction failed for %s: %s", image_path, e, exc_info=True)
            return ""

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        if not PDF_AVAILABLE:
            return ""
        try:
            chunks = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    chunks.append(page_text)
            return "\n".join(chunks).strip()
        except Exception:
            return ""

    # ── Lab value extraction ───────────────────────────────────────────────────

    def extract_lab_values(self, text: str) -> Dict[str, float]:
        """Parse numeric lab values from OCR text."""
        values: Dict[str, float] = {}
        text_lower = text.lower()

        # Blood pressure pattern: 120/80 or 120 / 80
        bp_match = re.search(r'(\d{2,3})\s*/\s*(\d{2,3})', text)
        if bp_match:
            sys_val = int(bp_match.group(1))
            dia_val = int(bp_match.group(2))
            if 60 <= sys_val <= 250 and 40 <= dia_val <= 150:
                values["systolic_bp"] = float(sys_val)
                values["diastolic_bp"] = float(dia_val)

        # Generic pattern: "Label : value unit" or "Label = value"
        number_pattern = re.compile(
            r'([a-z][a-z0-9\s\-/()]{2,40}?)\s*[:\-=]\s*(\d+\.?\d*)\s*([a-z/%µ]*)',
            re.IGNORECASE
        )

        for match in number_pattern.finditer(text_lower):
            label = match.group(1).strip()
            try:
                value = float(match.group(2))
            except ValueError:
                continue

            for param_name, param_info in LAB_RANGES.items():
                if any(key in label for key in param_info["key"]):
                    values[param_name] = value
                    break

        return values

    def extract_keywords(self, text: str) -> List[str]:
        """Extract medically relevant keywords from text."""
        medical_keywords = [
            "anemia", "diabetes", "hypertension", "infection", "fever",
            "inflammation", "deficiency", "elevated", "low", "high",
            "abnormal", "normal", "borderline", "critical", "positive",
            "negative", "reactive", "non-reactive", "dehydration",
            "cholesterol", "thyroid", "kidney", "liver", "blood",
            "urine", "cbc", "complete blood count", "lipid profile",
            # PATCH: expanded medical keywords
            "dengue", "malaria", "covid", "tuberculosis", "crp",
            "esr", "platelet", "hemoglobin", "creatinine", "proteinuria",
            "ketones", "ferritin", "vitamin d", "vitamin b12",
        ]
        text_lower = text.lower()
        return [kw for kw in medical_keywords if kw in text_lower]

    # ── Condition analysis ─────────────────────────────────────────────────────

    def analyze_lab_values(self, lab_values: Dict[str, float]) -> Dict[str, Any]:
        """Apply condition rules to extracted lab values."""
        detected_conditions = []
        abnormal_values = []
        overall_risk = "low"

        for rule in CONDITION_RULES:
            try:
                if rule["check"](lab_values):
                    severity = rule["severity"](lab_values)
                    detected_conditions.append({
                        "condition": rule["condition"],
                        "severity": severity,
                        "advice": rule["advice"],
                        "risk": rule["risk"],
                    })
                    if rule["risk"] == "high":
                        overall_risk = "high"
                    elif rule["risk"] == "medium" and overall_risk != "high":
                        overall_risk = "medium"
            except Exception:
                continue

        # Build abnormal value list
        for param, value in lab_values.items():
            if param not in LAB_RANGES:
                continue
            info = LAB_RANGES[param]
            low_ref, high_ref = info.get("both", info.get("male", (None, None)))
            if low_ref is None:
                continue
            status = "normal"
            if value < low_ref:
                status = "low"
            elif value > high_ref:
                status = "high"
            if status != "normal":
                abnormal_values.append({
                    "parameter": param.replace("_", " ").title(),
                    "value": value,
                    "unit": info["unit"],
                    "status": status,
                    "reference": f"{low_ref}–{high_ref} {info['unit']}",
                })

        return {
            "detected_conditions": detected_conditions,
            "abnormal_values": abnormal_values,
            "overall_risk": overall_risk,
        }

    def generate_report_summary(
        self,
        text: str,
        lab_values: Dict[str, float],
        analysis: Dict[str, Any],
    ) -> str:
        """Generate a human-readable summary of the report."""
        conditions = analysis.get("detected_conditions", [])
        abnormal   = analysis.get("abnormal_values", [])

        if not conditions and not abnormal:
            if lab_values:
                return "Lab values extracted. All parameters appear within normal reference ranges."
            return "Medical report processed. No specific abnormalities detected from available text."

        parts = []
        if conditions:
            names = [c["condition"] for c in conditions]
            parts.append(f"Detected indicators: {', '.join(names)}.")
        if abnormal:
            ab_str = ", ".join(
                f"{a['parameter']} ({a['status'].upper()}: {a['value']} {a['unit']})"
                for a in abnormal[:5]
            )
            parts.append(f"Abnormal values: {ab_str}.")
        parts.append("Please consult a qualified healthcare provider for interpretation.")
        base_summary = " ".join(parts)

        # PATCH: professional formatted summary appended after base summary
        try:
            report_type        = self.detect_report_type(text)
            specialist         = self.recommend_specialist(conditions)
            risk               = analysis.get("overall_risk", "low").upper()
            risk_emoji         = {"HIGH": "\u26a0\ufe0f", "MEDIUM": "\u26a0", "LOW": "\u2705"}.get(risk, "\u2139")
            critical_alerts    = self.detect_critical_values(lab_values)
            follow_up          = "Follow up with your specialist within 1-2 weeks." if risk == "HIGH" else "Schedule a routine follow-up."

            formatted = (
                f"\n\n\U0001f4cb **Report Type:** {report_type.title()}\n"
                f"\U0001f50d **Findings:** {', '.join(c['condition'] for c in conditions) if conditions else 'No significant findings'}\n"
                f"{risk_emoji} **Risk Level:** {risk}\n"
            )
            if abnormal:
                ab_list = "; ".join(
                    f"{a['parameter']} ({a['status'].upper()}: {a['value']} {a['unit']})"
                    for a in abnormal[:5]
                )
                formatted += f"\U0001f9ea **Abnormal Parameters:** {ab_list}\n"
            if critical_alerts:
                formatted += "\U0001f6a8 **CRITICAL:** " + "; ".join(a["alert"] for a in critical_alerts) + "\n"
            formatted += (
                f"\U0001f469\u200d\u2695\ufe0f **Recommended Specialist:** {specialist}\n"
                f"\U0001f4cc **Suggested Follow-Up:** {follow_up}"
            )
            return base_summary + formatted
        except Exception:
            return base_summary

    # ── Main entry point ───────────────────────────────────────────────────────

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process an uploaded medical file and return structured analysis."""
        extracted_text = ""
        ocr_error      = ""
        file_lower     = file_path.lower()

        # PATCH: reset per-file state
        self._last_ocr_confidence = 0.0
        self._last_image_quality  = "unknown"

        # Extract text — PDF first (no Tesseract needed), then image OCR
        if file_lower.endswith(".pdf"):
            extracted_text = self.extract_text_from_pdf(file_path)

        if not extracted_text:
            try:
                extracted_text = self.extract_text_from_image(file_path)
            except RuntimeError as e:
                ocr_error = str(e)
                logger.error("OCR unavailable: %s", ocr_error)
            except Exception as e:
                ocr_error = f"OCR processing error: {e}"
                logger.error("OCR failed: %s", e)

        # PATCH: apply OCR text normalization immediately after extraction
        if extracted_text:
            extracted_text = self.normalize_ocr_text(extracted_text)

        # If no text could be extracted
        if not extracted_text or len(extracted_text.strip()) < 15:
            # Give a specific message if we know Tesseract is the problem
            if not TESSERACT_STATUS["available"] or ocr_error:
                user_error = (
                    ocr_error if ocr_error else TESSERACT_STATUS.get("error", "")
                )
                install_hint = (
                    " To enable image OCR, install Tesseract from: "
                    "https://github.com/UB-Mannheim/tesseract/wiki (Windows) "
                    "or run 'sudo apt install tesseract-ocr' (Linux)."
                )
                return {
                    "success": False,
                    "error": user_error + install_hint,
                    "error_type": "tesseract_not_installed",
                    "extracted_text": "",
                    "lab_values": {},
                    "detected_conditions": [],
                    "abnormal_values": [],
                    "summary": "OCR engine not available. PDF text-based reports will work without Tesseract.",
                    "overall_risk": "unknown",
                    "keywords": [],
                    "confidence": 0,
                    "ocr_status": {
                        "pytesseract_installed": PYTESSERACT_INSTALLED,
                        "tesseract_available": TESSERACT_STATUS["available"],
                        "tesseract_path": TESSERACT_STATUS["path"],
                    },
                }
            # Generic extraction failure (image too blurry, no text, etc.)
            return {
                "success": False,
                "error": (
                    "Could not extract readable text from this file. "
                    "Please ensure the image is clear and well-lit, or upload a text-based PDF."
                ),
                "error_type": "extraction_failed",
                "extracted_text": "",
                "lab_values": {},
                "detected_conditions": [],
                "abnormal_values": [],
                "summary": "Text extraction failed. Please upload a clearer image or PDF.",
                "overall_risk": "unknown",
                "keywords": [],
                "confidence": 0,
            }

        # Analyze
        lab_values = self.extract_lab_values(extracted_text)
        keywords   = self.extract_keywords(extracted_text)
        analysis   = self.analyze_lab_values(lab_values)
        summary    = self.generate_report_summary(extracted_text, lab_values, analysis)

        # PATCH: run new enrichment helpers
        conditions             = analysis["detected_conditions"]
        critical_alerts        = self.detect_critical_values(lab_values)
        recommended_specialist = self.recommend_specialist(conditions)
        report_type            = self.detect_report_type(extracted_text)

        # Primary condition
        primary    = conditions[0]["condition"] if conditions else "General Health Report"
        confidence = min(95, 60 + len(lab_values) * 5 + len(conditions) * 8)

        return {
            "success":    True,
            "disease":    primary,
            "condition":  primary,
            "summary":    summary,
            "extracted_text":   extracted_text[:2000],
            "lab_values":        lab_values,
            "detected_conditions": conditions,
            "abnormal_values":   analysis["abnormal_values"],
            "overall_risk":      analysis["overall_risk"],
            "risk":              analysis["overall_risk"],
            "keywords":          keywords,
            "confidence":        confidence,
            "precautions":       [c["advice"] for c in conditions],
            "medicines":         [],
            "recommendations":   [c["advice"] for c in conditions] or [
                "Consult a qualified healthcare provider for full interpretation."
            ],
            # PATCH: new optional enrichment fields (additive only)
            "ocr_confidence":        self._last_ocr_confidence,
            "report_type":           report_type,
            "critical_alerts":       critical_alerts,
            "recommended_specialist": recommended_specialist,
            "image_quality":         self._last_image_quality,
        }
