"""
Tests for wellbin.core.scraper module.
"""

from collections import defaultdict
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from wellbin.core.scraper import WellbinMedicalDownloader


class TestWellbinMedicalDownloader:
    """Tests for WellbinMedicalDownloader class."""

    @pytest.fixture
    def downloader(self, temp_dir):
        """Create a WellbinMedicalDownloader instance for testing."""
        return WellbinMedicalDownloader(
            email="test@example.com",
            password="testpassword",
            headless=True,
            limit_studies=5,
            study_types=["FhirStudy"],
            output_dir=str(temp_dir),
        )

    def test_downloader_initialization(self, downloader, temp_dir):
        """Test downloader initialization."""
        assert downloader.email == "test@example.com"
        assert downloader.password == "testpassword"
        assert downloader.headless is True
        assert downloader.limit_studies == 5
        assert downloader.study_types == ["FhirStudy"]
        assert downloader.output_dir == str(temp_dir)

    def test_downloader_default_values(self, temp_dir):
        """Test downloader with default values."""
        downloader = WellbinMedicalDownloader(
            email="test@example.com", password="testpassword"
        )

        assert downloader.headless is True
        assert downloader.limit_studies is None
        assert downloader.study_types == ["FhirStudy"]
        assert downloader.output_dir == "downloads"

    def test_study_config(self, downloader):
        """Test study type configuration."""
        config = downloader.study_config

        assert "FhirStudy" in config
        assert "DicomStudy" in config
        assert config["FhirStudy"]["name"] == "lab"
        assert config["DicomStudy"]["name"] == "imaging"

    @patch("wellbin.core.scraper.webdriver.Chrome")
    def test_setup_driver_headless(self, mock_chrome, downloader):
        """Test driver setup in headless mode."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        downloader.setup_driver()

        assert downloader.driver == mock_driver
        mock_chrome.assert_called_once()

        # Check that headless option was added
        options_call = mock_chrome.call_args[1]["options"]
        assert any("--headless" in str(arg) for arg in options_call.arguments)

    @patch("wellbin.core.scraper.webdriver.Chrome")
    def test_setup_driver_visible(self, mock_chrome, temp_dir):
        """Test driver setup in visible mode."""
        downloader = WellbinMedicalDownloader(
            email="test@example.com",
            password="testpassword",
            headless=False,
            output_dir=str(temp_dir),
        )

        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        downloader.setup_driver()

        assert downloader.driver == mock_driver
        # Should not have headless argument
        options_call = mock_chrome.call_args[1]["options"]
        assert not any("--headless" in str(arg) for arg in options_call.arguments)

    def test_parse_date_from_text(self, downloader):
        """Test date parsing from various text formats."""
        date_patterns = [
            r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
            r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",
            r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b",
            r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b",
        ]
        month_map = {
            "Jan": "01",
            "Feb": "02",
            "Mar": "03",
            "Apr": "04",
            "May": "05",
            "Jun": "06",
            "Jul": "07",
            "Aug": "08",
            "Sep": "09",
            "Oct": "10",
            "Nov": "11",
            "Dec": "12",
        }

        # Test DD/MM/YYYY format
        result = downloader.parse_date_from_text(
            "Date: 04/06/2024", date_patterns, month_map
        )
        assert result == "20240604"

        # Test YYYY-MM-DD format
        result = downloader.parse_date_from_text(
            "Date: 2024-06-04", date_patterns, month_map
        )
        assert result == "20240604"

        # Test Month DD, YYYY format
        result = downloader.parse_date_from_text(
            "Date: Jun 04, 2024", date_patterns, month_map
        )
        assert result == "20240604"

        # Test no date found
        result = downloader.parse_date_from_text(
            "No date here", date_patterns, month_map
        )
        assert result is None

    def test_extract_date_from_study_id(self, downloader):
        """Test extracting date from study ID."""
        # Test YYYYMMDD format
        result = downloader.extract_date_from_study_id("study_20240604_abc123")
        assert result == "20240604"

        # Test YYYY-MM-DD format
        result = downloader.extract_date_from_study_id("study_2024-06-04_abc123")
        assert result == "20240604"

        # Test no date pattern
        result = downloader.extract_date_from_study_id("study_abc123")
        assert result is None

        # Test invalid date
        result = downloader.extract_date_from_study_id(
            "study_20241301_abc123"
        )  # Invalid month
        assert result is None

    def test_generate_filename(self, downloader):
        """Test filename generation with deduplication."""
        # Reset counters for clean test
        downloader.date_counters = defaultdict(int)

        # First file
        filename1 = downloader.generate_filename("20240604", "FhirStudy")
        assert filename1 == "20240604-lab-0.pdf"

        # Second file same date and type
        filename2 = downloader.generate_filename("20240604", "FhirStudy")
        assert filename2 == "20240604-lab-1.pdf"

        # Different type, same date
        filename3 = downloader.generate_filename("20240604", "DicomStudy")
        assert filename3 == "20240604-imaging-0.pdf"

        # Different date, same type
        filename4 = downloader.generate_filename("20240605", "FhirStudy")
        assert filename4 == "20240605-lab-0.pdf"

    def test_generate_filename_unknown_date(self, downloader):
        """Test filename generation with unknown date."""
        downloader.date_counters = defaultdict(int)

        filename = downloader.generate_filename("unknown", "FhirStudy")
        assert filename == "20240101-lab-0.pdf"  # Should use fallback date

    @patch("wellbin.core.scraper.requests.Session.get")
    def test_download_pdf_success(
        self, mock_get, downloader, mock_study_info, temp_dir
    ):
        """Test successful PDF download."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"fake pdf content"]
        mock_get.return_value = mock_response

        result = downloader.download_pdf(mock_study_info)

        assert result is not None
        assert result.endswith(".pdf")

        # Check that file was created
        from pathlib import Path

        pdf_path = Path(result)
        assert pdf_path.exists()
        assert pdf_path.read_bytes() == b"fake pdf content"

    @patch("wellbin.core.scraper.requests.Session.get")
    def test_download_pdf_http_error(self, mock_get, downloader, mock_study_info):
        """Test PDF download with HTTP error."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = downloader.download_pdf(mock_study_info)

        assert result is None

    @patch("wellbin.core.scraper.requests.Session.get")
    def test_download_pdf_exception(self, mock_get, downloader, mock_study_info):
        """Test PDF download with exception."""
        mock_get.side_effect = requests.RequestException("Network error")

        result = downloader.download_pdf(mock_study_info)

        assert result is None

    @patch.object(WellbinMedicalDownloader, "login")
    @patch.object(WellbinMedicalDownloader, "get_study_links")
    @patch.object(WellbinMedicalDownloader, "get_pdf_from_study")
    @patch.object(WellbinMedicalDownloader, "download_pdf")
    def test_scrape_studies_success(
        self,
        mock_download,
        mock_get_pdf,
        mock_get_links,
        mock_login,
        downloader,
        mock_study_links,
    ):
        """Test successful study scraping workflow."""
        # Mock successful login
        mock_login.return_value = True

        # Mock study links
        mock_get_links.return_value = mock_study_links

        # Mock PDF info
        mock_pdf_info = {
            "url": "https://test.com/test.pdf",
            "text": "Test PDF",
            "study_url": "https://wellbin.co/study/123",
            "study_type": "FhirStudy",
            "study_date": "20240604",
        }
        mock_get_pdf.return_value = [mock_pdf_info]

        # Mock successful download
        mock_download.return_value = "/path/to/downloaded.pdf"

        result = downloader.scrape_studies()

        assert len(result) == len(mock_study_links)
        mock_login.assert_called_once()
        mock_get_links.assert_called_once()
        assert mock_get_pdf.call_count == len(mock_study_links)
        assert mock_download.call_count == len(mock_study_links)

    @patch.object(WellbinMedicalDownloader, "login")
    def test_scrape_studies_login_failure(self, mock_login, downloader):
        """Test scraping with login failure."""
        mock_login.return_value = False

        result = downloader.scrape_studies()

        assert result == []
        mock_login.assert_called_once()

    @patch.object(WellbinMedicalDownloader, "login")
    @patch.object(WellbinMedicalDownloader, "get_study_links")
    def test_scrape_studies_no_links(self, mock_get_links, mock_login, downloader):
        """Test scraping with no study links found."""
        mock_login.return_value = True
        mock_get_links.return_value = []

        result = downloader.scrape_studies()

        assert result == []

    def test_scrape_studies_driver_cleanup(self, downloader):
        """Test that driver is properly cleaned up after scraping."""
        mock_driver = Mock()
        downloader.driver = mock_driver

        # Mock login failure to trigger cleanup
        with patch.object(downloader, "login", return_value=False):
            downloader.scrape_studies()

        mock_driver.quit.assert_called_once()
