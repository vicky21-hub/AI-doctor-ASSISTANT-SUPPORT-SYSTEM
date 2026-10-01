"""
input_validator.py - Medical input validation system.

Validates:
  - Severity ratings (1-10)
  - Duration (hours, days, weeks, months)
  - Body locations
  - Temperature readings
  - Medical measurements
"""

import re
from typing import Tuple, Optional, Dict, List
from utils.text_normalizer import TextNormalizer, SEVERITY_LEVELS, DURATION_PATTERNS, BODY_PARTS


class InputValidator:
    """Validate medical input responses."""

    @staticmethod
    def validate_severity(response: str) -> Tuple[bool, Optional[int], str]:
        """
        Validate severity rating response.
        
        Returns:
            (is_valid, severity_value, error_message)
        """
        if not response or not response.strip():
            return False, None, "Please provide a rating."

        response_lower = response.lower().strip()

        # Try to parse as number
        numbers = re.findall(r'\d+', response_lower)
        if numbers:
            try:
                severity = int(numbers[0])
                if 1 <= severity <= 10:
                    return True, severity, ""
                else:
                    return False, None, f"Severity must be between 1-10, not {severity}."
            except ValueError:
                pass

        # Try word-based severity
        for level, score in SEVERITY_LEVELS.items():
            if level in response_lower:
                return True, score, ""

        return False, None, "Please rate severity as a number (1-10) or word (mild, moderate, severe)."

    @staticmethod
    def validate_duration(response: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Validate duration response.
        
        Returns:
            (is_valid, duration_dict, error_message)
        """
        if not response or not response.strip():
            return False, None, "Please provide a duration."

        response_lower = response.lower().strip()

        # Extract number
        numbers = re.findall(r'\d+', response_lower)
        if not numbers:
            return False, None, "Please include a number (e.g., '2 days', '3 weeks')."

        value = int(numbers[0])
        if value <= 0:
            return False, None, "Duration must be positive."

        # Extract unit
        for unit, keywords in DURATION_PATTERNS.items():
            for keyword in keywords:
                if keyword in response_lower:
                    duration_dict = {
                        "value": value,
                        "unit": unit
                    }
                    return True, duration_dict, ""

        return False, None, "Specify duration unit: hours, days, weeks, or months."

    @staticmethod
    def validate_body_part(response: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate body part response.
        
        Returns:
            (is_valid, canonical_body_part, error_message)
        """
        if not response or not response.strip():
            return False, None, "Please specify a body part."

        response_lower = response.lower().strip()

        # Check against all body parts
        for canonical, aliases in BODY_PARTS.items():
            for alias in aliases:
                if response_lower.find(alias) != -1:
                    return True, canonical, ""

        # Try fuzzy matching for common body parts
        common_parts = ["head", "chest", "stomach", "back", "leg", "arm", "knee", "shoulder"]
        for part in common_parts:
            if part in response_lower:
                return True, part, ""

        return False, None, "Please specify a valid body part (e.g., head, chest, stomach, leg)."

    @staticmethod
    def validate_yes_no(response: str) -> Tuple[bool, Optional[bool], str]:
        """
        Validate yes/no response.
        
        Returns:
            (is_valid, answer, error_message)
        """
        if not response or not response.strip():
            return False, None, "Please answer yes or no."

        response_lower = response.lower().strip()

        # Yes variants
        if any(word in response_lower for word in ["yes", "yeah", "yep", "sure", "true", "correct", "y"]):
            return True, True, ""

        # No variants
        if any(word in response_lower for word in ["no", "nope", "false", "incorrect", "n", "not"]):
            return True, False, ""

        return False, None, "Please answer 'yes' or 'no'."

    @staticmethod
    def validate_temperature(response: str) -> Tuple[bool, Optional[float], str]:
        """
        Validate temperature reading.
        
        Returns:
            (is_valid, temperature_value, error_message)
        """
        if not response or not response.strip():
            return False, None, "Please provide a temperature reading."

        response_lower = response.lower().strip()

        # Extract number
        numbers = re.findall(r'\d+\.?\d*', response_lower)
        if not numbers:
            return False, None, "Please provide a numerical temperature value."

        try:
            temp = float(numbers[0])

            # Reasonable temperature range in Celsius (36-40) or Fahrenheit (96-104)
            if (36 <= temp <= 40) or (96 <= temp <= 104):
                return True, temp, ""
            else:
                return False, None, f"Temperature {temp} seems unusual. Please verify."

        except ValueError:
            return False, None, "Could not parse temperature."

    @staticmethod
    def validate_symptom_response(response: str) -> Tuple[bool, str]:
        """
        Validate that response mentions symptoms (not random text).
        
        Returns:
            (contains_symptom, error_message)
        """
        if not response or len(response.strip()) < 3:
            return False, "Please describe your symptoms more clearly."

        # This is a simple check - just ensure it's not obviously wrong
        # Could be extended with symptom keyword matching
        return True, ""

    @staticmethod
    def validate_medical_history(response: str) -> Tuple[bool, str]:
        """
        Validate medical history response.
        
        Returns:
            (is_valid, error_message)
        """
        if not response or not response.strip():
            return False, "Please provide some information about your medical history."

        # Simple validation - just checking it's not empty
        if len(response.strip()) < 5:
            return False, "Please provide more details about your medical history."

        return True, ""

    @staticmethod
    def validate_medication_response(response: str) -> Tuple[bool, str]:
        """
        Validate medication-related response.
        
        Returns:
            (is_valid, error_message)
        """
        if not response or not response.strip():
            return False, "Please answer about your medications."

        return True, ""

    @staticmethod
    def validate_exposure_response(response: str) -> Tuple[bool, str]:
        """
        Validate exposure/contact history response.
        
        Returns:
            (is_valid, error_message)
        """
        if not response or not response.strip():
            return False, "Please provide information about potential exposures."

        return True, ""

    @staticmethod
    def get_validation_error_message(field_type: str) -> str:
        """Get generic error message for a field type."""
        messages = {
            "severity": "Please rate from 1-10 (1=mild, 10=severe)",
            "duration": "Please specify duration (e.g., 2 hours, 3 days, 1 week)",
            "location": "Please specify a body part",
            "temperature": "Please provide temperature (e.g., 38.5°C or 101°F)",
            "yes_no": "Please answer 'yes' or 'no'",
        }
        return messages.get(field_type, "Invalid input. Please try again.")

    @staticmethod
    def get_retry_prompt(field_type: str) -> str:
        """Get a retry prompt for a failed validation."""
        prompts = {
            "severity": "Please rate your symptom severity on a scale of 1 to 10, where 1 is mild and 10 is severe.",
            "duration": "How long have you had this symptom? Please specify (hours, days, weeks, or months).",
            "location": "Which part of your body is affected? Please be specific.",
            "temperature": "What is your temperature? Please provide a numerical value.",
            "yes_no": "Please answer with 'yes' or 'no'.",
        }
        return prompts.get(field_type, "Could you clarify that for me?")


class ValidatingInputParser:
    """Parse and validate user responses in a single pass."""

    @staticmethod
    def parse_severity_with_validation(response: str) -> Tuple[bool, Optional[int], str]:
        """Parse and validate severity in one step."""
        is_valid, severity, error = InputValidator.validate_severity(response)
        return is_valid, severity, error

    @staticmethod
    def parse_duration_with_validation(response: str) -> Tuple[bool, Optional[Dict], str]:
        """Parse and validate duration in one step."""
        is_valid, duration, error = InputValidator.validate_duration(response)
        return is_valid, duration, error

    @staticmethod
    def parse_location_with_validation(response: str) -> Tuple[bool, Optional[str], str]:
        """Parse and validate location in one step."""
        is_valid, location, error = InputValidator.validate_body_part(response)
        return is_valid, location, error
