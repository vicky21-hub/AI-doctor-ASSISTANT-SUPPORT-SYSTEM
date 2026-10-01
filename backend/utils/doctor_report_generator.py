"""
doctor_report_generator.py - Generate professional medical reports and guidance.

Creates:
  - Patient Summary
  - Detailed Analysis
  - Risk Assessment
  - Treatment Recommendations
  - Follow-up Guidance
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class DoctorReportGenerator:
    """Generate professional medical reports."""

    @staticmethod
    def generate_consultation_report(
        primary_diagnosis: str,
        confidence: int,
        symptoms: List[str],
        location: Optional[str],
        severity: Optional[int],
        duration: Optional[Dict],
        history: Optional[str],
        disease_record: Optional[Dict],
        alternative_diagnoses: Optional[List[Dict]] = None,
    ) -> str:
        """
        Generate a comprehensive medical consultation report.
        
        Returns:
            Formatted report string
        """
        
        report = ""
        report += DoctorReportGenerator._generate_header()
        report += DoctorReportGenerator._generate_patient_summary(
            symptoms, location, severity, duration
        )
        report += DoctorReportGenerator._generate_clinical_assessment(
            primary_diagnosis, confidence, alternative_diagnoses
        )
        report += DoctorReportGenerator._generate_disease_details(
            disease_record, primary_diagnosis
        )
        report += DoctorReportGenerator._generate_risk_assessment(disease_record)
        report += DoctorReportGenerator._generate_recommendations(disease_record)
        report += DoctorReportGenerator._generate_warning_signs(disease_record)
        report += DoctorReportGenerator._generate_footer()
        
        return report

    @staticmethod
    def _generate_header() -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        header = "═" * 60 + "\n"
        header += "AI DOCTOR CONSULTATION REPORT\n"
        header += "═" * 60 + "\n"
        header += f"Generated: {timestamp}\n"
        header += "This is a preliminary assessment, not a medical diagnosis.\n"
        header += "─" * 60 + "\n\n"
        return header

    @staticmethod
    def _generate_patient_summary(
        symptoms: List[str],
        location: Optional[str],
        severity: Optional[int],
        duration: Optional[Dict],
    ) -> str:
        """Generate patient symptom summary."""
        summary = "**PATIENT SUMMARY**\n\n"
        
        summary += "**Chief Complaints:**\n"
        for i, symptom in enumerate(symptoms, 1):
            summary += f"  {i}. {symptom.capitalize()}\n"
        
        if location:
            summary += f"\n**Primary Location:** {location}\n"
        
        if severity:
            summary += f"**Severity Level:** {severity}/10 "
            if severity >= 8:
                summary += "(Severe)\n"
            elif severity >= 5:
                summary += "(Moderate)\n"
            else:
                summary += "(Mild)\n"
        
        if duration:
            value = duration.get("value")
            unit = duration.get("unit")
            summary += f"**Duration:** {value} {unit}\n"
        
        summary += "\n"
        return summary

    @staticmethod
    def _generate_clinical_assessment(
        primary_diagnosis: str,
        confidence: int,
        alternative_diagnoses: Optional[List[Dict]],
    ) -> str:
        """Generate clinical assessment and diagnosis."""
        assessment = "**CLINICAL ASSESSMENT**\n\n"
        
        assessment += f"**Most Likely Diagnosis:** {primary_diagnosis}\n"
        assessment += f"**Confidence Level:** {confidence}%\n\n"
        
        if alternative_diagnoses:
            assessment += "**Other Possible Conditions:**\n"
            for alt in alternative_diagnoses[:3]:
                disease = alt.get("disease", "Unknown")
                conf = alt.get("confidence", 0)
                assessment += f"  • {disease} ({conf}% match)\n"
        
        assessment += "\n"
        return assessment

    @staticmethod
    def _generate_disease_details(
        disease_record: Optional[Dict],
        disease_name: str,
    ) -> str:
        """Generate disease description and details."""
        if not disease_record:
            return ""
        
        details = "**DISEASE INFORMATION**\n\n"
        
        # Description
        description = disease_record.get("description", "")
        if description:
            details += f"**What is {disease_name}?**\n{description}\n\n"
        
        # Causes
        causes = disease_record.get("causes", [])
        if causes:
            details += "**Common Causes:**\n"
            for cause in causes[:5]:
                details += f"  • {cause}\n"
            details += "\n"
        
        # Symptoms
        all_symptoms = disease_record.get("symptoms", [])
        if all_symptoms:
            details += "**Typical Symptoms:**\n"
            for symptom in all_symptoms[:6]:
                details += f"  • {symptom}\n"
            details += "\n"
        
        return details

    @staticmethod
    def _generate_risk_assessment(disease_record: Optional[Dict]) -> str:
        """Generate risk level assessment."""
        if not disease_record:
            return ""
        
        risk = "**RISK ASSESSMENT**\n\n"
        
        risk_level = disease_record.get("risk_level", "medium").upper()
        risk += f"**Risk Level:** {risk_level}\n"
        
        if risk_level == "HIGH":
            risk += "⚠️ This condition requires immediate medical attention.\n"
        elif risk_level == "MEDIUM":
            risk += "⚠️ This condition requires prompt medical evaluation.\n"
        else:
            risk += "ℹ️ This condition can often be managed with proper care.\n"
        
        risk += "\n"
        return risk

    @staticmethod
    def _generate_recommendations(disease_record: Optional[Dict]) -> str:
        """Generate treatment and lifestyle recommendations."""
        if not disease_record:
            return ""
        
        rec = "**RECOMMENDED ACTIONS**\n\n"
        
        # Doctor type
        doctor_type = disease_record.get("doctor_type", "General Physician")
        rec += f"**Consult:** {doctor_type}\n\n"
        
        # Tests
        tests = disease_record.get("recommended_tests", [])
        if tests:
            rec += "**Recommended Tests:**\n"
            for test in tests[:5]:
                rec += f"  • {test}\n"
            rec += "\n"
        
        # OTC Medicines (only if appropriate)
        medicines = disease_record.get("medicines", [])
        if medicines and disease_record.get("risk_level") != "high":
            rec += "**Over-The-Counter Options** (with doctor approval):\n"
            for medicine in medicines[:4]:
                rec += f"  • {medicine}\n"
            rec += "\n"
        
        # Precautions
        precautions = disease_record.get("precautions", [])
        if precautions:
            rec += "**Important Precautions:**\n"
            for precaution in precautions[:5]:
                rec += f"  • {precaution}\n"
            rec += "\n"
        
        # Diet
        diet = disease_record.get("diet", [])
        if diet:
            rec += "**Dietary Recommendations:**\n"
            for item in diet[:5]:
                rec += f"  • {item}\n"
            rec += "\n"
        
        # Home Remedies
        remedies = disease_record.get("home_remedies", [])
        if remedies and disease_record.get("risk_level") != "high":
            rec += "**Home Remedies** (complementary to medical care):\n"
            for remedy in remedies[:4]:
                rec += f"  • {remedy}\n"
            rec += "\n"
        
        return rec

    @staticmethod
    def _generate_warning_signs(disease_record: Optional[Dict]) -> str:
        """Generate emergency warning signs."""
        warning = "**⚠️ EMERGENCY WARNING SIGNS**\n\n"
        
        if not disease_record:
            warning += "Seek immediate medical attention if:\n"
            warning += "  • Symptoms worsen rapidly\n"
            warning += "  • Difficulty breathing develops\n"
            warning += "  • Chest pain or pressure occurs\n"
            warning += "  • Severe dizziness or fainting\n"
            return warning
        
        is_emergency = disease_record.get("emergency", False)
        
        if is_emergency:
            warning += "🚨 This condition can be LIFE-THREATENING.\n"
            warning += "Seek IMMEDIATE medical attention if:\n"
        else:
            warning += "Seek immediate medical attention if:\n"
        
        # Generic warning signs
        warning += "  • Difficulty breathing or shortness of breath worsens\n"
        warning += "  • Chest pain, pressure, or tightness\n"
        warning += "  • Severe dizziness, confusion, or fainting\n"
        warning += "  • Severe bleeding or uncontrolled bleeding\n"
        warning += "  • High fever (>40°C / 104°F) with confusion\n"
        warning += "  • Severe allergic reactions (swelling of face/throat)\n"
        warning += "  • Loss of consciousness\n"
        warning += "  • Severe persistent vomiting or inability to drink fluids\n"
        
        warning += "\n"
        return warning

    @staticmethod
    def _generate_footer() -> str:
        """Generate report footer with disclaimers."""
        footer = "─" * 60 + "\n"
        footer += "**IMPORTANT DISCLAIMER**\n\n"
        footer += "⚠️ This is NOT a medical diagnosis. This assessment is for\n"
        footer += "informational purposes only and should NOT replace consultation\n"
        footer += "with a qualified healthcare professional.\n\n"
        footer += "Please consult a licensed physician for:\n"
        footer += "  • Proper diagnosis and treatment plans\n"
        footer += "  • Prescription medications\n"
        footer += "  • Detailed examination and testing\n"
        footer += "  • Medical history review\n\n"
        footer += "In case of emergency, call emergency services immediately.\n"
        footer += "═" * 60 + "\n"
        return footer

    @staticmethod
    def generate_quick_response(
        primary_diagnosis: str,
        confidence: int,
        disease_record: Optional[Dict],
    ) -> str:
        """Generate quick response for chat."""
        
        response = f"Based on your symptoms, the most likely condition is **{primary_diagnosis}** "
        response += f"(confidence: {confidence}%).\n\n"
        
        if disease_record:
            description = disease_record.get("description", "")
            if description:
                response += f"**What this means:** {description}\n\n"
            
            doctor = disease_record.get("doctor_type", "General Physician")
            risk = disease_record.get("risk_level", "medium")
            
            if risk == "high":
                response += f"⚠️ **This requires prompt medical attention.** Please consult a {doctor} as soon as possible.\n\n"
            else:
                response += f"👨‍⚕️ **Next step:** Schedule an appointment with a {doctor}.\n\n"
            
            # Quick recommendations
            medicines = disease_record.get("medicines", [])
            if medicines and risk != "high":
                response += f"**Common OTC options:** {', '.join(medicines[:2])}\n\n"
            
            precautions = disease_record.get("precautions", [])
            if precautions:
                response += f"**Key precautions:** {precautions[0]}\n\n"
        
        response += "⚠️ **Disclaimer:** This is not a medical diagnosis. Please consult a licensed healthcare professional.\n"
        
        return response

    @staticmethod
    def generate_follow_up_guidance(disease_record: Optional[Dict]) -> str:
        """Generate follow-up care guidance."""
        
        guidance = "**FOLLOW-UP GUIDANCE**\n\n"
        
        if not disease_record:
            guidance += "Follow up with your doctor if symptoms:\n"
            guidance += "  • Don't improve in 1-2 weeks\n"
            guidance += "  • Get worse\n"
            guidance += "  • Change in character\n"
            return guidance
        
        risk_level = disease_record.get("risk_level", "medium")
        
        if risk_level == "high":
            guidance += "⚠️ Seek medical attention IMMEDIATELY.\n"
        elif risk_level == "medium":
            guidance += "Schedule an appointment with your doctor within 24-48 hours.\n"
        else:
            guidance += "Schedule a doctor's appointment if symptoms persist beyond 1 week.\n"
        
        guidance += "\n**During Treatment:**\n"
        guidance += "  • Take prescribed medications exactly as instructed\n"
        guidance += "  • Follow all precautions strictly\n"
        guidance += "  • Monitor symptoms for any changes\n"
        guidance += "  • Rest adequately\n"
        guidance += "  • Stay hydrated\n"
        
        guidance += "\n**When to Seek Help Again:**\n"
        guidance += "  • If new symptoms develop\n"
        guidance += "  • If symptoms worsen despite treatment\n"
        guidance += "  • If you develop signs of complications\n"
        guidance += "  • If you have concerns about side effects\n"
        
        return guidance
