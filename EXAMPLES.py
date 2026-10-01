"""
QUICK START EXAMPLES - AI Doctor Assistant Enhanced System

This file shows practical examples of how to use each new component.
Run these examples to test the system.
"""

# ==================== EXAMPLE 1: Text Normalization ====================

def example_text_normalization():
    """Demonstrate text normalization capabilities."""
    from backend.utils.text_normalizer import TextNormalizer
    
    normalizer = TextNormalizer()
    
    print("=" * 60)
    print("EXAMPLE 1: TEXT NORMALIZATION")
    print("=" * 60)
    
    # Spell correction examples
    test_cases = {
        "hedache": "headache",
        "psoasis": "psoriasis",
        "diabtes": "diabetes",
        "fevor": "fever",
        "diarea": "diarrhea",
    }
    
    print("\n1. Spell Correction:")
    for wrong, correct in test_cases.items():
        result = normalizer.spell_correct(wrong)
        print(f"   {wrong:15} → {result:15} ({'✓' if correct in result else '✗'})")
    
    # Severity parsing
    print("\n2. Severity Parsing:")
    severity_tests = ["8", "severe", "mild", "moderate", "10"]
    for test in severity_tests:
        severity, is_valid = normalizer.parse_severity(test)
        print(f"   '{test:10}' → Severity: {severity:2} (Valid: {is_valid})")
    
    # Duration parsing
    print("\n3. Duration Parsing:")
    duration_tests = ["2 hours", "3 days", "1 week", "2 months"]
    for test in duration_tests:
        duration, is_valid = normalizer.parse_duration(test)
        if is_valid:
            print(f"   '{test:15}' → {duration['value']} {duration['unit']}")
        else:
            print(f"   '{test:15}' → INVALID")
    
    # Disease matching
    print("\n4. Disease Name Matching (Fuzzy):")
    disease_tests = ["psoasis", "diabtes", "asthma", "hypertention"]
    for test in disease_tests:
        disease = normalizer.fuzzy_match_disease(test)
        print(f"   '{test:15}' → '{disease}'")
    
    # Body part extraction
    print("\n5. Body Part Extraction:")
    text_tests = [
        "My knee hurts when walking",
        "I have chest pain and shoulder pain",
        "My head and neck are sore",
    ]
    for text in text_tests:
        parts = normalizer.extract_body_parts(text)
        print(f"   '{text}'")
        print(f"      → {', '.join(parts)}")


# ==================== EXAMPLE 2: Disease Question Trees ====================

def example_disease_question_trees():
    """Demonstrate disease-specific question trees."""
    from backend.utils.disease_question_trees import DiseaseQuestionTree
    
    print("\n" + "=" * 60)
    print("EXAMPLE 2: DISEASE-SPECIFIC QUESTION TREES")
    print("=" * 60)
    
    diseases = ["Fever", "Psoriasis", "Chest Pain", "Migraine", "Anxiety"]
    stages = ["location", "severity", "duration", "history"]
    
    for disease in diseases:
        print(f"\n{disease.upper()}:")
        
        for stage in stages:
            # Check if this stage should be skipped
            if DiseaseQuestionTree.should_skip_stage(disease, stage):
                print(f"  {stage:10} → [SKIPPED - location-agnostic disease]")
                continue
            
            questions = DiseaseQuestionTree.get_questions_for_disease(disease, stage)
            print(f"  {stage:10} → {questions[0] if questions else 'N/A'}")


# ==================== EXAMPLE 3: Input Validation ====================

def example_input_validation():
    """Demonstrate input validation."""
    from backend.utils.input_validator import InputValidator
    
    print("\n" + "=" * 60)
    print("EXAMPLE 3: INPUT VALIDATION")
    print("=" * 60)
    
    # Severity validation
    print("\n1. Severity Validation:")
    severity_tests = [
        ("8", True, "Valid number"),
        ("4 months", False, "Invalid - duration not severity"),
        ("severe", True, "Valid word"),
        ("100", False, "Out of range"),
        ("", False, "Empty"),
    ]
    
    for test, expected_valid, description in severity_tests:
        is_valid, severity, error = InputValidator.validate_severity(test)
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"   {status} '{test:15}' → Valid: {is_valid:5} ({description})")
        if not is_valid:
            print(f"      Error: {error}")
    
    # Duration validation
    print("\n2. Duration Validation:")
    duration_tests = [
        ("3 days", True),
        ("2 hours", True),
        ("1 week", True),
        ("4 months", True),
        ("just now", False),
        ("7", False),
    ]
    
    for test, expected_valid in duration_tests:
        is_valid, duration, error = InputValidator.validate_duration(test)
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"   {status} '{test:15}' → Valid: {is_valid}")
    
    # Body location validation
    print("\n3. Body Location Validation:")
    location_tests = [
        ("knee", True),
        ("my shoulder", True),
        ("left arm", True),
        ("xyz", False),
        ("", False),
    ]
    
    for test, expected_valid in location_tests:
        is_valid, location, error = InputValidator.validate_body_part(test)
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"   {status} '{test:15}' → Valid: {is_valid} (Location: {location})")
    
    # Yes/No validation
    print("\n4. Yes/No Validation:")
    yn_tests = [
        ("yes", True),
        ("no", True),
        ("yeah sure", True),
        ("nope", True),
        ("maybe", False),
    ]
    
    for test, expected_valid in yn_tests:
        is_valid, answer, error = InputValidator.validate_yes_no(test)
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"   {status} '{test:15}' → Valid: {is_valid} (Answer: {answer})")


# ==================== EXAMPLE 4: Medical Reasoning ====================

def example_medical_reasoning():
    """Demonstrate medical reasoning engine."""
    from backend.utils.medical_reasoning_engine import MedicalReasoningEngine
    from backend.services.knowledge_service import get_diseases
    
    print("\n" + "=" * 60)
    print("EXAMPLE 4: MEDICAL REASONING ENGINE")
    print("=" * 60)
    
    # Initialize
    diseases = get_diseases("human")
    engine = MedicalReasoningEngine(diseases)
    
    # Test case 1: Migraine
    print("\nTest Case 1: Migraine")
    print("-" * 40)
    
    analysis = engine.analyze_symptoms(
        symptoms=["headache", "nausea"],
        location="forehead",
        severity=8,
        duration={"value": 2, "unit": "hours"},
    )
    
    print(f"Primary Diagnosis: {analysis['primary_diagnosis']}")
    print(f"Confidence: {analysis['confidence']}%")
    print(f"Risk Level: {analysis['risk_level']}")
    print(f"Emergency: {analysis['requires_emergency']}")
    print(f"\nAlternative Diagnoses:")
    for alt in analysis['alternative_diagnoses']:
        print(f"  - {alt['disease']}: {alt['confidence']}%")
    
    # Test case 2: Psoriasis
    print("\nTest Case 2: Psoriasis")
    print("-" * 40)
    
    analysis = engine.analyze_symptoms(
        symptoms=["itchy skin", "red patches", "dry skin"],
        location="elbow",
        severity=6,
        duration={"value": 3, "unit": "months"},
    )
    
    print(f"Primary Diagnosis: {analysis['primary_diagnosis']}")
    print(f"Confidence: {analysis['confidence']}%")
    print(f"Risk Level: {analysis['risk_level']}")


# ==================== EXAMPLE 5: Conversation Memory ====================

def example_conversation_memory():
    """Demonstrate conversation memory tracking."""
    from backend.services.enhanced_ai_doctor_engine import ConversationMemory
    
    print("\n" + "=" * 60)
    print("EXAMPLE 5: CONVERSATION MEMORY")
    print("=" * 60)
    
    # Create and populate memory
    memory = ConversationMemory()
    
    print("\nInitial State:")
    print(f"  Symptoms: {memory.symptoms}")
    print(f"  Stage: {memory.current_stage}")
    
    # Simulate conversation progression
    print("\nAfter Step 1 (User describes symptoms):")
    memory.symptoms = ["headache", "nausea"]
    memory.current_stage = "asking_severity"
    print(f"  Symptoms: {memory.symptoms}")
    print(f"  Stage: {memory.current_stage}")
    
    print("\nAfter Step 2 (User rates severity):")
    memory.severity = 7
    memory.current_stage = "asking_duration"
    print(f"  Severity: {memory.severity}")
    print(f"  Stage: {memory.current_stage}")
    
    print("\nAfter Step 3 (User provides duration):")
    memory.duration = {"value": 2, "unit": "hours"}
    memory.current_stage = "diagnosis"
    print(f"  Duration: {memory.duration}")
    print(f"  Stage: {memory.current_stage}")
    
    # Serialize and deserialize
    print("\nSerialization Test:")
    serialized = memory.to_dict()
    print(f"  Serialized keys: {list(serialized.keys())}")
    
    new_memory = ConversationMemory()
    new_memory.from_dict(serialized)
    print(f"  Deserialized symptoms: {new_memory.symptoms}")
    print(f"  Deserialized severity: {new_memory.severity}")


# ==================== EXAMPLE 6: Full Consultation Flow ====================

def example_full_consultation():
    """Demonstrate a complete consultation flow."""
    from backend.services.enhanced_ai_doctor_engine import EnhancedAIDoctorEngine
    
    print("\n" + "=" * 60)
    print("EXAMPLE 6: COMPLETE CONSULTATION FLOW")
    print("=" * 60)
    
    engine = EnhancedAIDoctorEngine()
    
    # Simulate a conversation
    messages = [
        "I have a persistent headache and nausea",
        "I'd say it's about 7 out of 10",
        "It's been going on for 2 hours",
        "No previous issues like this",
    ]
    
    state = None
    
    for i, message in enumerate(messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"User: {message}")
        
        result = engine.process_message(message, state)
        
        print(f"\nAI: {result['reply'][:200]}...")
        print(f"Stage: {result['state']['current_stage']}")
        print(f"Emergency: {result['emergency']}")
        print(f"Is Diagnosis: {result['is_diagnosis']}")
        
        state = result['state']


# ==================== MAIN - Run All Examples ====================

if __name__ == "__main__":
    """Run all examples."""
    
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "AI DOCTOR ASSISTANT - EXAMPLES GUIDE" + " " * 12 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        example_text_normalization()
        example_disease_question_trees()
        example_input_validation()
        example_medical_reasoning()
        example_conversation_memory()
        example_full_consultation()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
