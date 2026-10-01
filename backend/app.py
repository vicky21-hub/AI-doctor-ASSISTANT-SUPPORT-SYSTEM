"""
app.py — AI Health Assistant Flask Backend (Production-Ready)
Run: python app.py
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai_health")

_DEFAULT_SECRET = "ai-health-secret-change-in-production-2024"
_FLASK_ENV = os.environ.get("FLASK_ENV", "development")

# ── Task 9: SECRET_KEY guard ───────────────────────────────────────────────────
_secret_key = os.environ.get("SECRET_KEY", _DEFAULT_SECRET)
if _FLASK_ENV == "production" and _secret_key == _DEFAULT_SECRET:
    raise RuntimeError(
        "SECRET_KEY is set to the default insecure value in production. "
        "Set a strong SECRET_KEY environment variable before deploying."
    )
if _secret_key == _DEFAULT_SECRET:
    logger.warning(
        "SECRET_KEY is using the default development value. "
        "Set a strong SECRET_KEY before deploying to production."
    )

# ── App factory ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
app.config["SECRET_KEY"] = _secret_key

# ── Task 10: CORS guard ────────────────────────────────────────────────────────
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
if _FLASK_ENV == "production" and allowed_origins == "*":
    raise RuntimeError(
        "ALLOWED_ORIGINS is set to wildcard '*' in production. "
        "Set ALLOWED_ORIGINS to your frontend domain before deploying."
    )
if allowed_origins == "*":
    logger.warning(
        "ALLOWED_ORIGINS=* allows any origin. "
        "Set ALLOWED_ORIGINS=https://yourdomain.com before deploying to production."
    )
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# ── Rate limiting ───────────────────────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per hour"],
    storage_uri="memory://",
)

# Expose limiter so blueprints can import it
app.extensions["limiter"] = limiter

# ── Blueprints ─────────────────────────────────────────────────────────────────
from routes.chat    import chat_bp
from routes.upload  import upload_bp
from routes.analyze import analyze_bp
from routes.history import history_bp
from routes.predict import predict_bp
from routes.vet     import vet_bp
from routes.auth    import auth_bp

app.register_blueprint(chat_bp,    url_prefix="/api")
app.register_blueprint(upload_bp,  url_prefix="/api")
app.register_blueprint(analyze_bp, url_prefix="/api")
app.register_blueprint(predict_bp, url_prefix="/api")
app.register_blueprint(vet_bp,     url_prefix="/api")
app.register_blueprint(history_bp, url_prefix="/api")
app.register_blueprint(auth_bp,    url_prefix="/api/auth")

# Apply per-route rate limits after blueprints are registered
for endpoint, limit_str in [
    ("auth.login",        "10 per minute"),
    ("auth.signup",       "5 per minute"),
    ("chat.chat",         "30 per minute"),
    ("upload.upload_file", "10 per minute"),
]:
    view_fn = app.view_functions.get(endpoint)
    if view_fn:
        limiter.limit(limit_str)(view_fn)

# Apply per-route rate limits after blueprints are registered
for endpoint, limit in {
    "login": "10 per minute",
    "signup": "5 per minute",
}.items():
    for name, view in app.view_functions.items():
        if name.endswith(endpoint):
            limiter.limit(limit)(view)
for endpoint, limit in {
    "chat": "30 per minute",
    "upload": "10 per minute",
}.items():
    for name, view in app.view_functions.items():
        if name.endswith(endpoint):
            limiter.limit(limit)(view)

# ── Health check ───────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "status": "ok",
        "message": "AI Health Assistant Backend is running",
        "version": "2.0.0",
        "endpoints": [
            "/api/health", "/api/chat", "/api/upload", "/api/analyze",
            "/api/predict", "/api/vet/chat", "/api/history",
            "/api/auth/login", "/api/auth/signup", "/api/auth/profile",
        ],
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "AI Health Assistant backend is running"})


@app.route("/api/health/ocr", methods=["GET"])
def health_ocr():
    """Diagnostic endpoint: reports Tesseract and pytesseract status."""
    from services.ocr_service import TESSERACT_STATUS, PYTESSERACT_INSTALLED, OCR_AVAILABLE
    return jsonify({
        "pytesseract_installed": PYTESSERACT_INSTALLED,
        "tesseract_available":   TESSERACT_STATUS["available"],
        "tesseract_version":     TESSERACT_STATUS["version"],
        "tesseract_path":        TESSERACT_STATUS["path"],
        "ocr_ready":             OCR_AVAILABLE,
        "error":                 TESSERACT_STATUS.get("error", ""),
        "pdf_ocr_available":     True,   # pdfplumber works without Tesseract
        "install_instructions": (
            "Windows: https://github.com/UB-Mannheim/tesseract/wiki  |  "
            "Linux: sudo apt install tesseract-ocr  |  "
            "Mac: brew install tesseract"
        ) if not OCR_AVAILABLE else "",
    })


# ── Error handlers ─────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum 16 MB allowed."}), 413


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    logger.info(f"Starting AI Health Assistant on port {port} (debug={debug})")
    app.run(debug=debug, host="0.0.0.0", port=port)
