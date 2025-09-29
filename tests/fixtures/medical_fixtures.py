"""
Medical data fixtures for testing.

These fixtures contain anonymized medical data based on real medical reports
but with all personal identifiers replaced with fictional data.

The fixtures maintain the medical structure and terminology to ensure
realistic testing of the PDF conversion and analysis functionality.
"""

from pathlib import Path
from typing import Dict, List

# Get the directory containing this file
FIXTURES_DIR = Path(__file__).parent

# Define fixture file paths
MEDICAL_DATA_DIR = FIXTURES_DIR / "medical_data"
LAB_REPORTS_DIR = MEDICAL_DATA_DIR / "lab_reports"
IMAGING_REPORTS_DIR = MEDICAL_DATA_DIR / "imaging_reports"

# Available test files
TEST_LAB_REPORTS = {
    "recent": "20230615-lab-0.md",  # Recent lab report with normal values
    "older": "20180425-lab-1.md",  # Older lab report with some elevated values
}

TEST_IMAGING_REPORTS = {
    "recent": "20240318-imaging-0.md",  # Recent MRI of knee with findings
    "older": "20190815-imaging-1.md",  # Older CT of chest, normal
}

# All available test files
ALL_TEST_FILES = {
    "lab": TEST_LAB_REPORTS,
    "imaging": TEST_IMAGING_REPORTS,
}


def get_fixture_path(report_type: str, age: str) -> Path:
    """
    Get the path to a specific test fixture file.

    Args:
        report_type: Either "lab" or "imaging"
        age: Either "recent" or "older"

    Returns:
        Path to the fixture file

    Raises:
        ValueError: If report_type or age is invalid
    """
    if report_type not in ALL_TEST_FILES:
        raise ValueError(
            f"Invalid report_type: {report_type}. Must be one of: {list(ALL_TEST_FILES.keys())}"
        )

    if age not in ALL_TEST_FILES[report_type]:
        raise ValueError(
            f"Invalid age for {report_type}: {age}. Must be one of: {list(ALL_TEST_FILES[report_type].keys())}"
        )

    filename = ALL_TEST_FILES[report_type][age]

    if report_type == "lab":
        return LAB_REPORTS_DIR / filename
    else:
        return IMAGING_REPORTS_DIR / filename


def get_fixture_content(report_type: str, age: str) -> str:
    """
    Get the content of a specific test fixture file.

    Args:
        report_type: Either "lab" or "imaging"
        age: Either "recent" or "older"

    Returns:
        Content of the fixture file as string
    """
    fixture_path = get_fixture_path(report_type, age)
    return fixture_path.read_text(encoding="utf-8")


def list_all_fixtures() -> Dict[str, List[str]]:
    """
    List all available fixture files.

    Returns:
        Dictionary mapping report types to lists of available files
    """
    result = {}
    for report_type, files in ALL_TEST_FILES.items():
        result[report_type] = list(files.values())
    return result


def get_fixtures_directory() -> Path:
    """Get the base fixtures directory path."""
    return FIXTURES_DIR


def get_medical_data_directory() -> Path:
    """Get the medical data fixtures directory path."""
    return MEDICAL_DATA_DIR


# Expected content patterns for validation
EXPECTED_PATTERNS = {
    "lab": {
        "headers": [
            "HEMOGRAMA COMPLETO",
            "SERIE ERITROCITARIA",
            "SERIE LEUCOCITARIA",
            "SERIE TROMBOCITARIA",
            "QUIMICA CLINICA",
        ],
        "measurements": ["Hemoglobina", "Hematocrito", "Glucosa", "Colesterol"],
        "units": ["g/dl", "mg/dl", "%", "10e9/L", "10e12/L"],
    },
    "imaging": {
        "headers": [
            "RESONANCIA MAGNETICA",
            "TOMOGRAFIA COMPUTADA",
            "HALLAZGOS",
            "CONCLUSION",
        ],
        "anatomical_terms": [
            "Menisco",
            "Ligamento",
            "Cartílago",
            "Parénquima pulmonar",
            "Mediastino",
        ],
        "findings": ["Sin alteraciones", "Conservado", "Normal"],
    },
}


def validate_fixture_content(report_type: str, content: str) -> bool:
    """
    Validate that fixture content contains expected medical patterns.

    Args:
        report_type: Type of report ("lab" or "imaging")
        content: Content to validate

    Returns:
        True if content appears to be valid medical report
    """
    if report_type not in EXPECTED_PATTERNS:
        return False

    patterns = EXPECTED_PATTERNS[report_type]

    # Check for at least some expected headers
    headers_found = sum(1 for header in patterns["headers"] if header in content)
    if headers_found == 0:
        return False

    # Check for medical report structure
    if "# Medical Report:" not in content:
        return False

    if "**Source File:**" not in content:
        return False

    return True
