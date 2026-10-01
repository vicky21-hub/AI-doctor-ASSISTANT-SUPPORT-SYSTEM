"""
DEPLOYMENT & CONFIGURATION GUIDE
AI Doctor Assistant - Production Ready System

This guide covers:
1. Environment Setup
2. Configuration
3. Deployment
4. Verification
5. Monitoring
"""

# ==================== STEP 1: ENVIRONMENT SETUP ====================

# Python Environment
# Required: Python 3.8+
# 
# Install dependencies:
# pip install -r backend/requirements.txt
#
# Required packages:
# - Flask (web framework)
# - scikit-learn (TF-IDF, cosine similarity)
# - rapidfuzz (fuzzy string matching)
# - requests (for external APIs if needed)
# - python-dotenv (for environment variables)

# ==================== STEP 2: CONFIGURATION ====================

# File: backend/.env
"""
# Server Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here
SERVER_PORT=5000

# Database
DATABASE_URL=sqlite:///health.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Features
ENABLE_CONVERSATION_MEMORY=True
ENABLE_EMAIL_ALERTS=False
MAX_CONVERSATION_LENGTH=50

# API Keys (if using external services)
OPENAI_API_KEY=optional
GOOGLE_PLACES_API_KEY=optional
"""

# ==================== STEP 3: DATABASE VERIFICATION ====================

def verify_disease_database():
    """Verify disease database is complete and ready."""
    from services.knowledge_service import get_diseases
    import json
    
    print("=" * 60)
    print("DATABASE VERIFICATION")
    print("=" * 60)
    
    diseases = get_diseases("human")
    
    print(f"\nTotal diseases loaded: {len(diseases)}")
    
    required_fields = [
        "disease_name",
        "description",
        "symptoms",
        "causes",
        "medicines",
        "precautions",
        "diet",
        "home_remedies",
        "recommended_tests",
        "doctor_type",
        "risk_level",
        "emergency",
    ]
    
    issues = []
    
    for disease in diseases:
        name = disease.get("disease_name", "Unknown")
        
        for field in required_fields:
            if field not in disease:
                issues.append(f"{name}: Missing field '{field}'")
            elif isinstance(disease[field], list) and len(disease[field]) == 0:
                issues.append(f"{name}: Empty list for '{field}'")
            elif isinstance(disease[field], str) and not disease[field].strip():
                issues.append(f"{name}: Empty string for '{field}'")
    
    if issues:
        print(f"\n⚠️  ISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✓ Database is complete and verified!")
    
    # Statistics
    print(f"\nDatabase Statistics:")
    print(f"  Total diseases: {len(diseases)}")
    total_symptoms = sum(len(d.get('symptoms', [])) for d in diseases)
    print(f"  Total symptoms: {total_symptoms}")
    print(f"  Avg symptoms per disease: {total_symptoms/len(diseases):.1f}")
    
    return len(issues) == 0


# ==================== STEP 4: MODULE VERIFICATION ====================

def verify_modules():
    """Verify all new modules are importable."""
    from importlib import import_module
    
    print("\n" + "=" * 60)
    print("MODULE VERIFICATION")
    print("=" * 60)
    
    modules = [
        ("utils.text_normalizer", "TextNormalizer"),
        ("utils.disease_question_trees", "DiseaseQuestionTree"),
        ("utils.input_validator", "InputValidator"),
        ("utils.medical_reasoning_engine", "MedicalReasoningEngine"),
        ("utils.doctor_report_generator", "DoctorReportGenerator"),
        ("services.enhanced_ai_doctor_engine", "EnhancedAIDoctorEngine"),
        ("ai.enhanced_disease_predictor", "EnhancedDiseasePredictor"),
    ]
    
    all_ok = True
    
    for module_name, class_name in modules:
        try:
            module = import_module(module_name)
            cls = getattr(module, class_name, None)
            if cls:
                print(f"✓ {module_name}.{class_name}")
            else:
                print(f"✗ {module_name}: Class {class_name} not found")
                all_ok = False
        except ImportError as e:
            print(f"✗ {module_name}: {str(e)}")
            all_ok = False
        except Exception as e:
            print(f"✗ {module_name}: {str(e)}")
            all_ok = False
    
    return all_ok


# ==================== STEP 5: FUNCTIONALITY TESTS ====================

def run_functionality_tests():
    """Run basic functionality tests."""
    from utils.text_normalizer import TextNormalizer
    from utils.disease_question_trees import DiseaseQuestionTree
    from utils.input_validator import InputValidator
    
    print("\n" + "=" * 60)
    print("FUNCTIONALITY TESTS")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Spell correction
    print("\n1. Spell Correction:")
    normalizer = TextNormalizer()
    test_cases = {
        "psoasis": "psoriasis",
        "hedache": "headache",
        "diabtes": "diabetes",
    }
    
    for wrong, correct in test_cases.items():
        result = normalizer.spell_correct(wrong)
        if correct in result.lower():
            print(f"   ✓ {wrong} → {correct}")
            tests_passed += 1
        else:
            print(f"   ✗ {wrong} → {result} (expected {correct})")
            tests_failed += 1
    
    # Test 2: Disease question trees
    print("\n2. Disease Question Trees:")
    try:
        questions = DiseaseQuestionTree.get_questions_for_disease("Migraine", "location")
        if questions:
            print(f"   ✓ Migraine questions loaded ({len(questions)} questions)")
            tests_passed += 1
        else:
            print(f"   ✗ No questions found for Migraine")
            tests_failed += 1
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        tests_failed += 1
    
    # Test 3: Input validation
    print("\n3. Input Validation:")
    is_valid, severity, _ = InputValidator.validate_severity("7")
    if is_valid and severity == 7:
        print(f"   ✓ Severity validation works")
        tests_passed += 1
    else:
        print(f"   ✗ Severity validation failed")
        tests_failed += 1
    
    is_valid, duration, _ = InputValidator.validate_duration("3 days")
    if is_valid and duration['value'] == 3:
        print(f"   ✓ Duration validation works")
        tests_passed += 1
    else:
        print(f"   ✗ Duration validation failed")
        tests_failed += 1
    
    print(f"\nTests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    
    return tests_failed == 0


# ==================== STEP 6: DEPLOYMENT CHECKLIST ====================

def show_deployment_checklist():
    """Show pre-deployment checklist."""
    
    print("\n" + "=" * 60)
    print("PRE-DEPLOYMENT CHECKLIST")
    print("=" * 60)
    
    checklist = [
        ("Python 3.8+ installed", "python --version"),
        ("All dependencies installed", "pip list | grep flask"),
        ("Database file exists", "ls -la backend/knowledge/human_diseases.json"),
        ("Flask app starts", "python backend/app.py"),
        ("API responds to requests", "curl http://localhost:5000/health"),
        ("Chat endpoint works", "curl -X POST http://localhost:5000/chat"),
        ("All modules importable", "python -c 'from utils.text_normalizer import ...'"),
        ("Database verified", "Check human_diseases.json completeness"),
        ("Environment variables set", "Check .env file"),
        ("Logging configured", "Check logs directory"),
        ("Error handling tested", "Test with invalid inputs"),
        ("SSL/HTTPS configured", "Check certificate files"),
        ("Rate limiting enabled", "Check flask-limiter config"),
        ("CORS configured", "Check flask-cors settings"),
        ("Monitoring configured", "Check prometheus/datadog setup"),
    ]
    
    print("\nPre-Deployment Steps:")
    for i, (task, command) in enumerate(checklist, 1):
        print(f"  [ ] {i:2}. {task}")
        if command:
            print(f"       Command: {command}")


# ==================== STEP 7: DOCKER DEPLOYMENT ====================

docker_compose_content = """
# File: docker-compose.yml for production deployment

version: '3.8'

services:
  ai-doctor-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=False
      - LOG_LEVEL=INFO
    volumes:
      - ./backend/knowledge:/app/knowledge:ro
      - ./logs:/app/logs
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - ai-doctor-backend
    restart: always
"""

# ==================== STEP 8: MONITORING SETUP ====================

monitoring_config = """
# File: backend/config/monitoring.py

import logging
from logging.handlers import RotatingFileHandler
import os

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# File handler for rotation
file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

# Metrics to track
METRICS = {
    "total_conversations": 0,
    "total_diagnoses": 0,
    "average_confidence": 0,
    "emergency_cases": 0,
    "response_times": [],
    "validation_failures": 0,
}
"""

# ==================== STEP 9: HEALTH CHECK ====================

def health_check():
    """Run system health check."""
    print("\n" + "=" * 60)
    print("SYSTEM HEALTH CHECK")
    print("=" * 60)
    
    checks = {
        "database": False,
        "modules": False,
        "functionality": False,
    }
    
    # Check database
    print("\nChecking database...")
    checks["database"] = verify_disease_database()
    
    # Check modules
    print("\nChecking modules...")
    checks["modules"] = verify_modules()
    
    # Check functionality
    print("\nRunning functionality tests...")
    checks["functionality"] = run_functionality_tests()
    
    # Summary
    print("\n" + "=" * 60)
    print("HEALTH CHECK SUMMARY")
    print("=" * 60)
    
    for check, status in checks.items():
        symbol = "✓" if status else "✗"
        print(f"{symbol} {check.upper()}: {'PASS' if status else 'FAIL'}")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("\n✓ SYSTEM IS READY FOR DEPLOYMENT")
    else:
        print("\n✗ SYSTEM HAS ISSUES - FIX BEFORE DEPLOYMENT")
    
    return all_passed


# ==================== MAIN: RUN ALL CHECKS ====================

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "AI DOCTOR - DEPLOYMENT VERIFICATION" + " " * 13 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        system_ready = health_check()
        
        if system_ready:
            print("\n" + "=" * 60)
            print("NEXT STEPS:")
            print("=" * 60)
            print("1. Review DEPLOYMENT_GUIDE.md")
            print("2. Set environment variables in .env")
            print("3. Configure nginx for HTTPS")
            print("4. Set up monitoring and alerting")
            print("5. Run: docker-compose up -d")
            print("6. Verify: curl http://localhost/health")
            print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DEPLOYMENT CHECK FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
