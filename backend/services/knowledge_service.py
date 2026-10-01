import json
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def load_json_file(filename: str) -> Any:
    path = BASE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Knowledge file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


HUMAN_DISEASES: List[Dict[str, Any]] = load_json_file("human_diseases.json")
ANIMAL_DISEASES: List[Dict[str, Any]] = load_json_file("animal_diseases.json")
MEDICINES: List[Dict[str, Any]] = load_json_file("medicines.json")
EMERGENCY_RULES: List[Dict[str, Any]] = load_json_file("emergency_rules.json")
SPECIALTIES: List[str] = load_json_file("specialties.json")
ANATOMY_SYSTEMS: List[Dict[str, Any]] = load_json_file("anatomy_systems.json")


def get_diseases(domain: str = "human") -> List[Dict[str, Any]]:
    return HUMAN_DISEASES if domain == "human" else ANIMAL_DISEASES


def find_disease(name: str, domain: str = "human") -> Optional[Dict[str, Any]]:
    diseases = get_diseases(domain)
    normalized = name.strip().lower()
    for disease in diseases:
        if disease["disease_name"].strip().lower() == normalized:
            return disease
    return None


def find_medicine(name: str) -> Optional[Dict[str, Any]]:
    normalized = name.strip().lower()
    for med in MEDICINES:
        if med["name"].strip().lower() == normalized:
            return med
    return None
