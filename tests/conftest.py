"""
Pytest configuration and common fixtures for wellbin tests.

Fixture Scope Strategy:
- module: Immutable data (env configs, static content) - created once per module
- function: Mutable objects or test state - fresh instance per test
"""

import pytest

from .fixtures.medical_fixtures import (
    get_fixture_content,
    get_medical_data_directory,
)

# ============================================================================
# Module-scoped fixtures for immutable data (performance optimization)
# ============================================================================


@pytest.fixture(scope="module")
def sample_env_config():
    """Sample environment configuration for testing.

    Module-scoped because this is immutable static data.
    """
    return {
        "WELLBIN_EMAIL": "test@example.com",
        "WELLBIN_PASSWORD": "testpassword",
        "WELLBIN_OUTPUT_DIR": "test_output",
        "WELLBIN_STUDY_TYPES": "FhirStudy",
        "WELLBIN_STUDY_LIMIT": "5",
        "WELLBIN_HEADLESS": "true",
        "WELLBIN_ENHANCED_MODE": "false",
    }


@pytest.fixture(scope="module")
def invalid_env_config():
    """Invalid environment configuration for testing validation.

    Module-scoped because this is immutable static data.
    """
    return {
        "WELLBIN_EMAIL": "your-email@example.com",  # Default invalid value
        "WELLBIN_PASSWORD": "your-password",  # Default invalid value
    }


@pytest.fixture(scope="module")
def sample_pdf_content():
    """Sample PDF content for converter tests.

    Module-scoped because this is immutable static data.
    """
    return b"%PDF-1.4 fake pdf content for testing"


@pytest.fixture(scope="module")
def mock_study_links():
    """Sample study links for scraper tests.

    Module-scoped because this is immutable static data.
    """
    return [
        "https://wellbin.co/study/123?type=FhirStudy",
        "https://wellbin.co/study/456?type=DicomStudy",
        "https://wellbin.co/study/789?type=FhirStudy",
    ]


@pytest.fixture(scope="module")
def medical_fixtures_dir():
    """Path to the medical test fixtures directory.

    Module-scoped because the path doesn't change.
    """
    return get_medical_data_directory()


@pytest.fixture(scope="module")
def sample_lab_report_recent():
    """Recent lab report fixture content.

    Module-scoped because file content is immutable during tests.
    """
    return get_fixture_content("lab", "recent")


@pytest.fixture(scope="module")
def sample_lab_report_older():
    """Older lab report fixture content.

    Module-scoped because file content is immutable during tests.
    """
    return get_fixture_content("lab", "older")


@pytest.fixture(scope="module")
def sample_imaging_report_recent():
    """Recent imaging report fixture content.

    Module-scoped because file content is immutable during tests.
    """
    return get_fixture_content("imaging", "recent")


@pytest.fixture(scope="module")
def sample_imaging_report_older():
    """Older imaging report fixture content.

    Module-scoped because file content is immutable during tests.
    """
    return get_fixture_content("imaging", "older")


@pytest.fixture(scope="module")
def all_fixture_reports():
    """All test fixture reports as a dictionary.

    Module-scoped because file content is immutable during tests.
    """
    return {
        "lab_recent": get_fixture_content("lab", "recent"),
        "lab_older": get_fixture_content("lab", "older"),
        "imaging_recent": get_fixture_content("imaging", "recent"),
        "imaging_older": get_fixture_content("imaging", "older"),
    }


# ============================================================================
# Function-scoped fixtures for mutable/per-test state
# ============================================================================


@pytest.fixture
def mock_study_info():
    """Sample study information for scraper tests.

    Function-scoped because PDFDownloadInfo is a mutable dataclass.
    """
    from wellbin.core.scraper import PDFDownloadInfo

    return PDFDownloadInfo(
        url="https://wellbin-uploads.s3.amazonaws.com/test.pdf",
        text="Test Lab Report",
        study_url="https://wellbin.co/study/123?type=FhirStudy",
        study_type="FhirStudy",
        study_date="20240604",
    )
