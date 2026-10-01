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
from database.health_db import save_report, save_history
from routes.auth import optional_auth

logger = logging.getLogger(__name__)

upload_bp = Blueprint("upload", __name__)
ocr_service = OCRService()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"}

# Magic bytes for allowed MIME types
_MAGIC = {
    b"\x25\x50\x44\x46": "pdf",           # %PDF
    b"\x89\x50\x4e\x47": "png",           # PNG
    b"\xff\xd8\xff":      "jpg",           # JPEG
    b"\x49\x49\x2a\x00": "tiff",          # TIFF little-endian
    b"\x4d\x4d\x00\x2a": "tiff",          # TIFF big-endian
    b"\x42\x4d":          "bmp",           # BMP
    b"\x52\x49\x46\x46": "webp",          # RIFF (WebP)
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _validate_magic(filepath: str) -> bool:
    """Return True if the file's magic bytes match a known safe type."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(8)
        for magic, _ in _MAGIC.items():
            if header[:len(magic)] == magic:
                return True
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

        try:
            ocr_result = ocr_service.process_file(filepath)
        except Exception as ocr_exc:
            # Task 12: log before cleanup so the error is traceable
            logger.error("[Upload] OCR failed for %s: %s", filename, ocr_exc, exc_info=True)
            raise
        finally:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                filepath = None

        result = enrich(ocr_result)

        user_id = getattr(g, "user_id", None)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
        save_report({
            "user_id":   user_id,
            "filename":  filename,
            "file_type": ext,
            "ocr_text":  result.get("extracted_text", ""),
            "analysis":  result,
        })

        if result.get("success") and result.get("disease"):
            save_history({
                "user_id":     user_id,
                "domain":      "human",
                "symptoms":    result.get("keywords", []),
                "disease":     result.get("disease", ""),
                "confidence":  result.get("confidence", 0),
                "risk_level":  result.get("risk_level", "low"),
                "emergency":   result.get("emergency", False),
                "doctor_type": result.get("doctor_type", "General Physician"),
                "additional_info": {
                    "source":            "report_upload",
                    "filename":          filename,
                    "report_type":       result.get("report_type", ""),
                    "lab_values":        result.get("lab_values", {}),
                    "abnormal_values":   result.get("abnormal_values", []),
                    "clinical_findings": result.get("clinical_findings", []),
                    "followup_tests":    result.get("followup_tests", []),
                    "critical_alerts":   result.get("critical_alerts", []),
                },
            })

        return jsonify(result)

    except Exception as e:
        # Task 12: always log filename so failed uploads are traceable
        logger.error("[Upload] Processing failed for %s: %s", filename, e, exc_info=True)
        return jsonify({"error": f"Upload processing failed: {str(e)}"}), 500
    finally:
        # Guarantee cleanup even if an unhandled exception escapes
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
