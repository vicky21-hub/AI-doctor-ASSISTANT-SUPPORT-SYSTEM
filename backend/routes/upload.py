"""
upload.py — File upload with OCR processing and database persistence.
Task 12: log filename + error before deletion so failures are traceable.
Task 13: validate file magic bytes (not just extension) to reject disguised files.
"""

import os
import logging
from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
from services.ocr_service import OCRService
from services.report_analyzer_service import enrich
from services.skin_analyzer_service import SkinAnalyzerService
from database.health_db import save_report, save_history
from routes.auth import optional_auth

logger = logging.getLogger(__name__)

upload_bp = Blueprint("upload", __name__)
ocr_service = OCRService()
skin_analyzer = SkinAnalyzerService()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "tiff", "bmp", "webp"}

# Magic bytes for allowed MIME types
_MAGIC = {
    b"\x25\x50\x44\x46": "pdf",           # %PDF
    b"\x89\x50\x4e\x47": "png",           # PNG
    b"\xff\xd8":          "jpg",           # JPEG (standard SOI marker)
    b"\x49\x49\x2a\x00": "tiff",          # TIFF little-endian
    b"\x4d\x4d\x00\x2a": "tiff",          # TIFF big-endian
    b"\x42\x4d":          "bmp",           # BMP
    b"\x52\x49\x46\x46": "webp",          # RIFF (WebP)
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _validate_magic(filepath: str) -> bool:
    """Return True if the file's magic bytes match a known safe type or verifies as an image."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(12)
        for magic, _ in _MAGIC.items():
            if header[:len(magic)] == magic:
                return True
        # Secondary check for valid images using PIL
        try:
            from PIL import Image
            with Image.open(filepath) as img:
                img.verify()
                return True
        except Exception:
            pass
        return False
    except Exception as exc:
        logger.warning("[Upload] Magic byte check failed for %s: %s", filepath, exc)
        return False


@upload_bp.route("/upload", methods=["POST"])
@optional_auth
def upload_file():
    filepath = None
    filename = "unknown"
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported file type. Use PDF, PNG, JPG, TIFF, or BMP."}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Task 13: reject files whose content doesn't match a safe magic signature
        if not _validate_magic(filepath):
            logger.warning("[Upload] Magic byte mismatch — rejecting %s", filename)
            return jsonify({"error": "File content does not match its extension. Upload rejected."}), 400

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
        is_image = ext in IMAGE_EXTENSIONS

        result = None

        # 1. If it's an image, check whether it exhibits skin visual features
        skin_features = skin_analyzer.detect_skin_and_features(filepath) if is_image else {}
        is_skin = skin_features.get("is_skin_image", False)

        # 2. Attempt OCR processing (for lab reports, prescriptions, test results)
        ocr_result = None
        try:
            ocr_result = ocr_service.process_file(filepath)
        except Exception as ocr_exc:
            logger.warning("[Upload] OCR attempt threw error for %s: %s", filename, ocr_exc)

        # Check if OCR found medical lab parameters or medical keywords
        has_lab_or_keywords = False
        if ocr_result and ocr_result.get("success"):
            has_lab_or_keywords = bool(
                ocr_result.get("lab_values")
                or len(ocr_result.get("keywords", [])) >= 2
                or ocr_result.get("report_type") not in ("general report", "")
            )

        # 3. Decision routing:
        # If OCR found genuine medical parameters -> Enrich lab report
        if ocr_result and ocr_result.get("success") and has_lab_or_keywords:
            result = enrich(ocr_result)
        elif is_image and is_skin:
            # If skin detected and no lab biomarkers -> Route to Skin & Dermatology Analyzer
            logger.info("[Upload] Skin detected in %s — routing to SkinAnalyzerService", filename)
            try:
                skin_result = skin_analyzer.analyze(filepath)
                if skin_result and skin_result.get("success"):
                    result = skin_result
            except Exception as skin_exc:
                logger.error("[Upload] Skin analyzer failed for %s: %s", filename, skin_exc, exc_info=True)

        # 4. If still no result, fallback to OCR result if it had any success, or try skin analyzer on any image
        if not result and is_image:
            try:
                skin_result = skin_analyzer.analyze(filepath)
                if skin_result and skin_result.get("success"):
                    result = skin_result
            except Exception:
                pass

        if not result:
            if ocr_result and ocr_result.get("success"):
                result = enrich(ocr_result)
            elif ocr_result:
                result = ocr_result
            else:
                result = {
                    "success": False,
                    "error": "Could not analyze the file. Please ensure the image is clear or upload a valid PDF report.",
                }

        user_id = getattr(g, "user_id", None)
        save_report({
            "user_id":   user_id,
            "filename":  filename,
            "file_type": ext,
            "ocr_text":  result.get("extracted_text", result.get("description", "")),
            "analysis":  result,
        })

        if result.get("success") and result.get("disease"):
            save_history({
                "user_id":     user_id,
                "domain":      "human",
                "symptoms":    result.get("keywords", result.get("possible_conditions", [])),
                "disease":     result.get("disease", ""),
                "confidence":  result.get("confidence", 0),
                "risk_level":  result.get("risk_level", "low"),
                "emergency":   result.get("emergency", False),
                "doctor_type": result.get("doctor_type", "General Physician"),
                "additional_info": {
                    "source":            result.get("source", "report_upload"),
                    "filename":          filename,
                    "report_type":       result.get("report_type", ""),
                    "care_category":     result.get("care_category", ""),
                    "lab_values":        result.get("lab_values", {}),
                    "abnormal_values":   result.get("abnormal_values", []),
                    "clinical_findings": result.get("clinical_findings", []),
                    "followup_tests":    result.get("followup_tests", []),
                    "critical_alerts":   result.get("critical_alerts", []),
                },
            })

        return jsonify(result)

    except Exception as e:
        logger.error("[Upload] Processing failed for %s: %s", filename, e, exc_info=True)
        return jsonify({"error": f"Upload processing failed: {str(e)}"}), 500
    finally:
        # Guarantee cleanup of uploaded file
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as rm_exc:
                logger.warning("[Upload] Could not remove temp file %s: %s", filepath, rm_exc)
