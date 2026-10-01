# AI Doctor Support - Testing Guide

## Quick Start Testing

### Test 1: Spell Correction & Symptom Recognition

**Test Case 1a: Single Symptom with Typo**
```
Input: "psoasis"
Expected: Disease name matched to "Psoriasis"
Verification Points:
  ✓ fuzzy_match_disease_name() returns ("Psoriasis", 88)
  ✓ extract_canonical_symptoms() returns psoriasis symptoms
  ✓ AI offers: "Did you mean Psoriasis?"
```

**Test Case 1b: Multiple Symptom Typos**
```
Input: "I have hedache and digziness"
Expected: 
  - "hedache" → "headache"
  - "digziness" → "dizziness"
Verification: AI understands both symptoms correctly
```

**Test Case 1c: Symptom Misspellings**
```
Test: "fevr", "coph", "stommach pain", "nusea"
Expected: All corrected to proper spellings
Command to test:
  from backend.ai.symptom_matcher import correct_spelling
  print(correct_spelling("I have a fevr and coph"))
  # Should output: "I have a fever and cough"
```

---

### Test 2: Disease Prediction - Never Single-Symptom Diagnosis

**Test Case 2a: Single Symptom - Should Ask More Questions**
```
Input: "fever"
Expected Output:
  - confidence: 0 (needs_more_info status)
  - reply includes: "Tell me more. Do you have..."
  - Asks about: cough, body pain, chills, breathing, etc.
  
NOT Expected: 
  - Pneumonia with 78% confidence
  - Malaria with 65% confidence
```

**Test Case 2b: Multi-Symptom - Should Diagnose**
```
Input Symptoms:
  - fever (38.5°C)
  - severe cough
  - chest pain when breathing
  - shortness of breath
  - fatigue for 3 days

Expected Output:
  - Top 1: Pneumonia (78%)
  - Top 2: Bronchitis (65%)
  - Top 3: Viral Fever (52%)
  
API Test:
  POST /api/predict
  {
    "symptoms": ["fever", "cough", "chest pain", "shortness of breath"],
    "severity": 8,
    "domain": "human"
  }
  
  Response should include all 3 predictions
```

**Test Case 2c: Diverse Confidence Scores**
```
Verify: Top 3 predictions have DIFFERENT confidence scores
Example ✅: 72%, 64%, 57% (gaps of 8% and 7%)
Example ❌: 72%, 72%, 71% (scores too similar - rerun prediction)
```

---

### Test 3: Doctor Report - No Empty Sections

**Test Case 3a: Report Generation**
```
Input: Pneumonia diagnosis with patient info
API Call:
  POST /api/generate_report
  {
    "predictions": [...],
    "patient_info": {"age": 35, "gender": "male"},
    "collected_info": {"symptoms": [...], "severity": 8}
  }

Verification Checklist:
  ✓ "What You Can Do" has 6-8 items (NO blanks)
  ✓ "Emergency Warning Signs" has 6-8 items (NO blanks)
  ✓ "Medical Disclaimers" has 6 items (NO blanks)
  ✓ "Medicines" has only non-empty items
  ✓ "Supplements" has only non-empty items
  ✓ No section with only header, no content
```

**Test Case 3b: Verify Actionable Items**
```
Check "What You Can Do" section for:
  ✓ "Rest adequately..." (generic)
  ✓ "Stay hydrated..." (generic)
  ✓ Home remedies (disease-specific)
  ✓ Diet recommendations (disease-specific)
  ✓ Doctor appointment timing (based on risk level)
  ✓ Medication guidance (if applicable)
  
None should be:
  - Empty strings
  - Just punctuation
  - Generic filler
```

---

### Test 4: Medicine & Supplements Complete Data

**Test Case 4a: All Diseases Have Supplements**
```
Code Test:
  import json
  with open('backend/knowledge/human_diseases.json') as f:
      diseases = json.load(f)
  
  for disease in diseases:
      assert 'supplements' in disease, f"{disease['disease_name']} missing supplements"
      assert len(disease['supplements']) > 0, f"{disease['disease_name']} has empty supplements"
      print(f"✓ {disease['disease_name']}: {disease['supplements']}")

Expected: 36 diseases all passing
```

**Test Case 4b: No Empty Arrays**
```
Code Test:
  for disease in diseases:
      assert disease['medicines'], "medicines empty"
      assert disease['supplements'], "supplements empty"
      assert disease['diet'], "diet empty"
      assert disease['precautions'], "precautions empty"
      # All assertions should pass
```

**Test Case 4c: Sample Disease Verification**
```
Test Dengue:
  ✓ medicines: ["Paracetamol", "ORS"]
  ✓ supplements: ["Vitamin C", "Papaya leaf extract"]
  ✓ diet: ["coconut water", "papaya leaf juice", ...]
  ✓ home_remedies: ["rest", "hydrate frequently"]
  
Test Anxiety:
  ✓ supplements: ["Magnesium", "L-Theanine", "Ashwagandha"]
```

---

### Test 5: Context-Aware Scoring

**Test Case 5a: Age-Based Adjustment**
```
Input: "difficulty breathing, wheezing, chest tightness"
  Patient 1: Age 5 (child)
  Patient 2: Age 35 (adult)
  Patient 3: Age 72 (elderly)

Expected Scoring:
  - Asthma higher confidence for child
  - Different risks for elderly (emphysema, COPD adjustment)
  
API Test:
  POST with patient_context: {"age": 5}
  POST with patient_context: {"age": 72}
  Compare confidence scores - should differ
```

**Test Case 5b: Medical History Integration**
```
Input: "weight gain, fatigue, cold intolerance"
  Patient A: Medical history: ["Diabetes"]
  Patient B: Medical history: ["Autoimmune disease"]

Expected:
  - Patient A: Higher Hypothyroidism confidence
  - Patient B: Different risk assessment
```

---

### Test 6: Frontend - Results Display

**Test Case 6a: Results Page Shows Top 3**
```
Navigate to Results Page with:
  {
    "top_conditions": [
      {"rank": 1, "name": "Dengue", "confidence": 72},
      {"rank": 2, "name": "Malaria", "confidence": 58},
      {"rank": 3, "name": "Typhoid", "confidence": 42}
    ]
  }

Verify:
  ✓ All 3 diseases displayed
  ✓ Confidence percentages shown
  ✓ Risk levels color-coded
  ✓ Emergency alerts visible if high risk
```

**Test Case 6b: Sections Auto-Hide if Empty**
```
If disease has no supplements:
  ✓ Supplements section not shown
  
If no recommended tests:
  ✓ Tests section not shown
  
Always shown (never empty):
  ✓ What You Can Do
  ✓ Medical Disclaimers
  ✓ Emergency Warnings (if high risk)
```

---

## Integration Testing

### End-to-End Flow Test

```
1. User sends: "I have psoriasis itch"
   ✓ Symptom matcher corrects/recognizes
   ✓ Suggests: "Did you mean Psoriasis?"

2. User confirms: "yes"
   ✓ Severity question asked

3. User answers: "7/10"
   ✓ Duration question asked

4. User answers: "3 weeks"
   ✓ Medical history question asked

5. User answers: "None"
   ✓ Prediction generated

6. Result shows:
   ✓ Psoriasis (92%) as top prediction
   ✓ Medications: [...non-empty...]
   ✓ Supplements: [...non-empty...]
   ✓ What you can do: [...6-8 items...]
   ✓ Disclaimers: [...6 items...]
```

---

## Performance Testing

### Test Response Times

```
Test 1: Spell Correction
  Code: correct_spelling("diebetes hedache fevr")
  Expected: < 100ms
  
Test 2: Disease Prediction
  Code: predictor.predict("fever cough", top_n=3)
  Expected: < 500ms
  
Test 3: Report Generation
  Code: DoctorReportGenerator.generate_consultation_report(...)
  Expected: < 300ms
```

---

## Edge Case Testing

### Test Case 1: Gibberish Input
```
Input: "asfasfsaf zzzzzz"
Expected: "I couldn't understand. Could you describe your symptom?"
Should NOT: Crash, return None, diagnose random disease
```

### Test Case 2: Empty Input
```
Input: ""
Expected: Error or prompt for input
Should NOT: Return diagnosis
```

### Test Case 3: Contradictory Symptoms
```
Input: "I feel warm (fever), but my body is freezing (chills), I have energy (fatigue)"
Expected: Still processes correctly, recognizes contradictions
Confidence: May be lower due to mixed signals
```

### Test Case 4: Very Long Input
```
Input: "I have..." + 500 words
Expected: Extracts key symptoms, doesn't crash
Performance: < 2 seconds
```

---

## Database Validation

### Validate human_diseases.json

```bash
# Check all required fields present
python3 << 'EOF'
import json

with open('backend/knowledge/human_diseases.json') as f:
    diseases = json.load(f)

required_fields = [
    'disease_name', 'description', 'symptoms', 'causes',
    'medicines', 'supplements', 'precautions', 'diet',
    'home_remedies', 'recommended_tests', 'doctor_type',
    'risk_level', 'body_system'
]

for disease in diseases:
    for field in required_fields:
        if field not in disease:
            print(f"❌ {disease['disease_name']} missing: {field}")
        elif not disease[field]:
            print(f"⚠️  {disease['disease_name']} empty: {field}")

print("✓ All validation complete")
EOF
```

---

## Regression Testing Checklist

Before each update, verify:

- [ ] Symptom spell correction still works
- [ ] Single symptoms don't give high confidence
- [ ] Top 3 predictions return different scores
- [ ] Report has no empty sections
- [ ] All diseases have supplements
- [ ] Emergency detection works
- [ ] No crashes on edge cases
- [ ] Frontend displays correctly
- [ ] API response times < 2s

---

## Test Data

### Sample Test Patients

**Patient A - Pneumonia Case**
```json
{
  "symptoms": ["fever", "cough", "chest pain", "shortness of breath"],
  "severity": 8,
  "duration": {"value": 3, "unit": "days"},
  "age": 45,
  "gender": "male",
  "medical_history": ["hypertension"],
  "expected_top": "Pneumonia"
}
```

**Patient B - Dengue Case**
```json
{
  "symptoms": ["high fever", "body pain", "joint pain", "rash"],
  "severity": 7,
  "duration": {"value": 4, "unit": "days"},
  "age": 28,
  "gender": "female",
  "exposure": "mosquito",
  "expected_top": "Dengue"
}
```

**Patient C - Anxiety Case**
```json
{
  "symptoms": ["anxiety", "rapid heartbeat", "sweating", "restlessness"],
  "severity": 6,
  "duration": {"value": 2, "unit": "weeks"},
  "age": 35,
  "gender": "female",
  "medical_history": ["stress"],
  "expected_top": "Anxiety"
}
```

---

## Success Criteria

✅ All tests passing = Production ready

- [ ] Phase 1: Spell correction tests (5/5 passing)
- [ ] Phase 5: Disease prediction tests (6/6 passing)
- [ ] Phase 6: Medicine/supplement tests (3/3 passing)
- [ ] Phase 7: Report format tests (4/4 passing)
- [ ] Phase 9: Frontend tests (2/2 passing)
- [ ] Integration test (end-to-end flow)
- [ ] Performance tests (all < 2s)
- [ ] Edge cases (5/5 handled)

---

**Test Environment**: Development  
**Last Updated**: June 6, 2026  
**Total Test Cases**: 30+
