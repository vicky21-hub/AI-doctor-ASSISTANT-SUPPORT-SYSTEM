"""
doctor_report_generator.py - Generate professional medical consultation reports.

Generates comprehensive doctor-style reports with:
  - Patient Summary (age, gender)
  - Collected Symptoms
  - Top Conditions with confidence percentages
  - Risk Level Assessment
  - Medicines & Supplements (OTC only)
  - Diet Plan
  - Recommended Tests
  - Doctor Specialist
  - Emergency Warning Signs
  - What You Can Do (actionable steps)
  - Medical Disclaimers (no empty sections)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class DoctorReportGenerator:
    """Generate professional medical consultation reports without empty sections."""

    @staticmethod
    def generate_consultation_report(
        predictions: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]] = None,
        collected_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive medical consultation report.
        
        Args:
            predictions: List of disease predictions from DiseasePredictor
            patient_info: Optional dict with age, gender, medical_history
            collected_info: Optional dict with severity, duration, location, etc.
        
        Returns:
            Dictionary with all report sections (only non-empty sections included)
        """
        
        if not predictions or predictions[0].get("disease_name") == "needs_more_info":
            return {
                "status": "insufficient_info",
                "timestamp": datetime.now().isoformat(),
                "message": "Insufficient information for reliable diagnosis",
                "recommendations": [
                    "Provide more detailed symptom descriptions",
                    "Answer diagnostic questions to gather more information",
                    "Specify symptom onset and duration",
                ],
            }
        
        top_condition = predictions[0]
        alternatives = predictions[1:3]  # Get 2nd and 3rd conditions
        
        report = {
            "status": "analysis_complete",
            "timestamp": datetime.now().isoformat(),
            "patient_summary": DoctorReportGenerator._generate_patient_summary(patient_info),
            "symptoms": DoctorReportGenerator._generate_symptoms_section(collected_info),
            "top_conditions": DoctorReportGenerator._generate_top_conditions(predictions),
            "risk_level": top_condition.get("risk_level", "medium").upper(),
            "emergency": top_condition.get("emergency", False),
        }
        
        # Add optional sections only if they have content
        medicines = DoctorReportGenerator._generate_medicines_section(top_condition)
        if medicines:
            report["medicines"] = medicines
        
        supplements = DoctorReportGenerator._generate_supplements_section(top_condition)
        if supplements:
            report["supplements"] = supplements
        
        diet = DoctorReportGenerator._generate_diet_plan(top_condition)
        if diet:
            report["diet_plan"] = diet
        
        tests = DoctorReportGenerator._generate_recommended_tests(top_condition)
        if tests:
            report["recommended_tests"] = tests
        
        report["doctor_specialist"] = top_condition.get("doctor_type", "General Physician")
        
        warnings = DoctorReportGenerator._generate_emergency_warnings(top_condition)
        if warnings:
            report["emergency_warning_signs"] = warnings
        
        actions = DoctorReportGenerator._generate_what_you_can_do(top_condition)
        if actions:
            report["what_you_can_do"] = actions
        
        report["medical_disclaimers"] = DoctorReportGenerator._generate_disclaimers()
        
        return report

    @staticmethod
    def _generate_patient_summary(patient_info: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Generate patient summary section."""
        summary = {}
        
        if patient_info:
            if patient_info.get("age"):
                summary["age"] = f"{patient_info['age']} years"
            if patient_info.get("gender"):
                summary["gender"] = patient_info["gender"]
            if patient_info.get("medical_history"):
                history = patient_info.get("medical_history", [])
                if history:
                    summary["medical_history"] = ", ".join(history)
        
        return summary if summary else {"status": "No specific patient info collected"}

    @staticmethod
    def _generate_symptoms_section(collected_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate collected symptoms section."""
        symptoms_info = {}
        
        if collected_info:
            if collected_info.get("symptoms"):
                symptoms_info["reported_symptoms"] = collected_info["symptoms"]
            if collected_info.get("severity"):
                symptoms_info["severity_1_to_10"] = collected_info["severity"]
            if collected_info.get("duration"):
                duration = collected_info["duration"]
                symptoms_info["duration"] = f"{duration.get('value', '')} {duration.get('unit', '')}"
            if collected_info.get("location"):
                symptoms_info["location"] = collected_info["location"]
        
        return symptoms_info if symptoms_info else {}

    @staticmethod
    def _generate_top_conditions(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate top 3 conditions with confidence scores."""
        conditions = []
        
        for i, pred in enumerate(predictions[:3]):
            if pred.get("disease_name") == "needs_more_info":
                continue
            
            conditions.append({
                "rank": i + 1,
                "name": pred.get("disease_name", "Unknown"),
                "confidence_percent": pred.get("confidence", 0),
                "description": pred.get("description", ""),
                "risk_level": pred.get("risk_level", "medium"),
            })
        
        return conditions

    @staticmethod
    def _generate_medicines_section(disease: Dict[str, Any]) -> Optional[List[str]]:
        """Generate OTC medicines section (only if not empty and not high-risk)."""
        medicines = disease.get("medicines", [])
        risk_level = disease.get("risk_level", "medium")
        
        # Filter out empty and duplicate items
        cleaned = [m for m in medicines if m and str(m).strip()]
        
        # Don't recommend medicines for high-risk conditions without doctor approval
        if risk_level.lower() == "high" and cleaned:
            return [f"⚠️ {m} (only with doctor approval)" for m in cleaned[:3]]
        
        return cleaned[:3] if cleaned else None

    @staticmethod
    def _generate_supplements_section(disease: Dict[str, Any]) -> Optional[List[str]]:
        """Generate supplements section (only if not empty)."""
        supplements = disease.get("supplements", [])
        
        # Filter out empty and duplicate items
        cleaned = [s for s in supplements if s and str(s).strip()]
        
        return cleaned[:4] if cleaned else None

    @staticmethod
    def _generate_diet_plan(disease: Dict[str, Any]) -> Optional[List[str]]:
        """Generate diet recommendations (only if not empty)."""
        diet = disease.get("diet", [])
        
        # Filter out empty items
        cleaned = [d for d in diet if d and str(d).strip()]
        
        return cleaned[:5] if cleaned else None

    @staticmethod
    def _generate_recommended_tests(disease: Dict[str, Any]) -> Optional[List[str]]:
        """Generate recommended tests (only if not empty)."""
        tests = disease.get("recommended_tests", [])
        
        # Filter out empty items
        cleaned = [t for t in tests if t and str(t).strip()]
        
        return cleaned[:4] if cleaned else None

    @staticmethod
    def _generate_emergency_warnings(disease: Dict[str, Any]) -> Optional[List[str]]:
        """Generate emergency warning signs (always include some)."""
        warnings = []
        
        is_emergency = disease.get("emergency", False)
        risk_level = disease.get("risk_level", "medium").lower()
        
        if is_emergency:
            warnings.append("🚨 SEEK IMMEDIATE EMERGENCY CARE")
        
        # Disease-specific warnings
        disease_name = disease.get("disease_name", "").lower()
        
        if "pneumonia" in disease_name or "asthma" in disease_name:
            warnings.extend([
                "Difficulty breathing or worsening shortness of breath",
                "Blue lips or fingernails",
                "Severe chest pain",
            ])
        elif "dengue" in disease_name or "malaria" in disease_name:
            warnings.extend([
                "Severe abdominal pain",
                "Persistent vomiting",
                "Bleeding from gums or nose",
                "Severe weakness or lethargy",
            ])
        elif "kidney" in disease_name:
            warnings.extend([
                "Severe flank pain unrelieved by position change",
                "Blood in urine with fever",
                "Inability to urinate",
            ])
        else:
            # Generic emergency signs
            warnings.extend([
                "Difficulty breathing or chest pain",
                "Loss of consciousness or severe confusion",
                "Severe allergic reaction (swelling of face/throat)",
                "High fever (>40°C / 104°F) with confusion",
                "Severe bleeding or uncontrolled hemorrhage",
                "Severe persistent vomiting or inability to drink",
            ])
        
        # Always add emergency number
        warnings.append("📞 Call emergency services (911/999/112) immediately")
        
        return list(set(warnings))  # Remove duplicates

    @staticmethod
    def _generate_what_you_can_do(disease: Dict[str, Any]) -> Optional[List[str]]:
        """Generate actionable steps for patient (at least 3 items, no empty bullet points)."""
        actions = []
        
        # Base actions (always applicable)
        actions.append("Rest adequately and allow your body to recover")
        actions.append("Stay hydrated - drink plenty of water and electrolyte solutions")
        actions.append("Monitor symptoms and keep a log of any changes")
        
        # Home remedies
        remedies = disease.get("home_remedies", [])
        cleaned_remedies = [r for r in remedies if r and str(r).strip()]
        if cleaned_remedies:
            actions.append(f"Try home remedies: {', '.join(cleaned_remedies[:2])}")
        
        # Diet-specific advice
        diet = disease.get("diet", [])
        cleaned_diet = [d for d in diet if d and str(d).strip()]
        if cleaned_diet:
            actions.append(f"Follow recommended diet: Include {', '.join(cleaned_diet[:2])}")
        
        # Risk-level specific actions
        risk_level = disease.get("risk_level", "medium").lower()
        if risk_level == "high":
            actions.append("Schedule urgent appointment with recommended specialist (within 24 hours)")
        elif risk_level == "medium":
            actions.append("Schedule doctor appointment within 3-5 days for proper evaluation")
        else:
            actions.append("Monitor for 1-2 weeks; see doctor if symptoms persist or worsen")
        
        # Medication guidance
        medicines = disease.get("medicines", [])
        if medicines and any(m for m in medicines if m and str(m).strip()):
            actions.append("Ask pharmacist about appropriate OTC options for symptom relief")
        
        # Prevention for future
        actions.append("Follow precautions to prevent recurrence or spread to others")
        
        # Ensure at least 3 different, non-empty actions
        final_actions = [a for a in actions if a and str(a).strip()]
        return final_actions[:8] if final_actions else None

    @staticmethod
    def _generate_disclaimers() -> List[str]:
        """Generate medical disclaimers (at least 4 items, no empty bullet points)."""
        disclaimers = [
            "This is NOT a medical diagnosis. Always consult a licensed healthcare professional for proper diagnosis and treatment.",
            "This assessment is for informational purposes only and should not replace professional medical advice.",
            "Over-the-counter medicines are recommendations only. Do not use without consulting a pharmacist or doctor.",
            "For persistent or worsening symptoms, seek immediate medical attention from a qualified physician.",
            "Individual medical needs vary; treatment plans must be personalized by a healthcare provider.",
            "In case of emergency, contact your local emergency services immediately.",
        ]
        
        return [d for d in disclaimers if d and str(d).strip()]

    @staticmethod
    def generate_text_report(report_dict: Dict[str, Any]) -> str:
        """Convert report dictionary to readable text format."""
        text_report = ""
        
        timestamp = report_dict.get("timestamp", "")
        text_report += "═" * 70 + "\n"
        text_report += "AI DOCTOR CONSULTATION REPORT\n"
        text_report += f"Generated: {timestamp}\n"
        text_report += "═" * 70 + "\n\n"
        
        # Patient Summary
        if report_dict.get("patient_summary"):
            text_report += "PATIENT SUMMARY\n"
            for key, value in report_dict["patient_summary"].items():
                text_report += f"  • {key.replace('_', ' ').title()}: {value}\n"
            text_report += "\n"
        
        # Symptoms
        if report_dict.get("symptoms"):
            text_report += "REPORTED SYMPTOMS\n"
            for key, value in report_dict["symptoms"].items():
                if isinstance(value, list):
                    text_report += f"  • {key.replace('_', ' ').title()}:\n"
                    for item in value:
                        text_report += f"    - {item}\n"
                else:
                    text_report += f"  • {key.replace('_', ' ').title()}: {value}\n"
            text_report += "\n"
        
        # Top Conditions
        if report_dict.get("top_conditions"):
            text_report += "TOP CONDITIONS (Ranked by Likelihood)\n"
            for cond in report_dict["top_conditions"]:
                text_report += f"  {cond['rank']}. {cond['name']} - {cond['confidence_percent']}% confidence\n"
                text_report += f"     Risk Level: {cond['risk_level'].upper()}\n"
                if cond.get("description"):
                    text_report += f"     {cond['description']}\n"
            text_report += "\n"
        
        # Risk Level
        text_report += f"OVERALL RISK LEVEL: {report_dict.get('risk_level', 'MEDIUM')}\n"
        if report_dict.get("emergency"):
            text_report += "⚠️  THIS IS AN EMERGENCY CONDITION\n"
        text_report += "\n"
        
        # Medicines
        if report_dict.get("medicines"):
            text_report += "RECOMMENDED OTC MEDICINES\n"
            for med in report_dict["medicines"]:
                text_report += f"  • {med}\n"
            text_report += "\n"
        
        # Supplements
        if report_dict.get("supplements"):
            text_report += "RECOMMENDED SUPPLEMENTS\n"
            for supp in report_dict["supplements"]:
                text_report += f"  • {supp}\n"
            text_report += "\n"
        
        # Diet
        if report_dict.get("diet_plan"):
            text_report += "DIET RECOMMENDATIONS\n"
            for food in report_dict["diet_plan"]:
                text_report += f"  • {food}\n"
            text_report += "\n"
        
        # Tests
        if report_dict.get("recommended_tests"):
            text_report += "RECOMMENDED TESTS\n"
            for test in report_dict["recommended_tests"]:
                text_report += f"  • {test}\n"
            text_report += "\n"
        
        # Doctor Specialist
        text_report += f"RECOMMENDED SPECIALIST: {report_dict.get('doctor_specialist', 'General Physician')}\n\n"
        
        # Emergency Warnings
        if report_dict.get("emergency_warning_signs"):
            text_report += "⚠️  EMERGENCY WARNING SIGNS - SEEK IMMEDIATE HELP IF:\n"
            for warning in report_dict["emergency_warning_signs"][:6]:
                text_report += f"  • {warning}\n"
            text_report += "\n"
        
        # What You Can Do
        if report_dict.get("what_you_can_do"):
            text_report += "WHAT YOU CAN DO\n"
            for action in report_dict["what_you_can_do"]:
                text_report += f"  • {action}\n"
            text_report += "\n"
        
        # Medical Disclaimers
        text_report += "MEDICAL DISCLAIMERS\n"
        for disclaimer in report_dict.get("medical_disclaimers", []):
            text_report += f"  • {disclaimer}\n"
        
        text_report += "═" * 70 + "\n"
        
        return text_report
