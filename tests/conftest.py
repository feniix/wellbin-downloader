"""
Pytest configuration and common fixtures for wellbin tests.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from .fixtures.medical_fixtures import (
    get_fixture_content,
    get_fixture_path,
    get_medical_data_directory,
    validate_fixture_content,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_env_config():
    """Sample environment configuration for testing."""
    return {
        "WELLBIN_EMAIL": "test@example.com",
        "WELLBIN_PASSWORD": "testpassword",
        "WELLBIN_OUTPUT_DIR": "test_output",
        "WELLBIN_STUDY_TYPES": "FhirStudy",
        "WELLBIN_STUDY_LIMIT": "5",
        "WELLBIN_HEADLESS": "true",
        "WELLBIN_ENHANCED_MODE": "false",
    }


@pytest.fixture
def invalid_env_config():
    """Invalid environment configuration for testing validation."""
    return {
        "WELLBIN_EMAIL": "your-email@example.com",  # Default invalid value
        "WELLBIN_PASSWORD": "your-password",  # Default invalid value
    }


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for converter tests."""
    return b"%PDF-1.4 fake pdf content for testing"


@pytest.fixture
def mock_study_links():
    """Sample study links for scraper tests."""
    return [
        "https://wellbin.co/study/123?type=FhirStudy",
        "https://wellbin.co/study/456?type=DicomStudy",
        "https://wellbin.co/study/789?type=FhirStudy",
    ]


@pytest.fixture
def mock_study_info():
    """Sample study information for scraper tests."""
    return {
        "url": "https://wellbin-uploads.s3.amazonaws.com/test.pdf",
        "text": "Test Lab Report",
        "study_url": "https://wellbin.co/study/123?type=FhirStudy",
        "study_type": "FhirStudy",
        "study_date": "20240604",
    }


@pytest.fixture
def medical_fixtures_dir():
    """Path to the medical test fixtures directory."""
    return get_medical_data_directory()


@pytest.fixture
def sample_lab_report_recent():
    """Recent lab report fixture content."""
    return get_fixture_content("lab", "recent")


@pytest.fixture
def sample_lab_report_older():
    """Older lab report fixture content."""
    return get_fixture_content("lab", "older")


@pytest.fixture
def sample_imaging_report_recent():
    """Recent imaging report fixture content."""
    return get_fixture_content("imaging", "recent")


@pytest.fixture
def sample_imaging_report_older():
    """Older imaging report fixture content."""
    return get_fixture_content("imaging", "older")


@pytest.fixture
def all_fixture_reports():
    """All test fixture reports as a dictionary."""
    return {
        "lab_recent": get_fixture_content("lab", "recent"),
        "lab_older": get_fixture_content("lab", "older"),
        "imaging_recent": get_fixture_content("imaging", "recent"),
        "imaging_older": get_fixture_content("imaging", "older"),
    }
