"""
Tests for wellbin.core.scraper module.
"""

from collections import defaultdict
from unittest.mock import Mock, patch

import pytest
import requests
from selenium.common.exceptions import NoSuchElementException

from wellbin.core.date_parser import (
    extract_date_from_study_id,
    is_valid_date,
    parse_date_from_text,
)
from wellbin.core.scraper import PDFDownloadInfo, WellbinMedicalDownloader


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
        downloader = WellbinMedicalDownloader(email="test@example.com", password="testpassword")

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
        """Test date parsing from various text formats using module-level function."""
        # Test DD/MM/YYYY format (uses default patterns)
        result = parse_date_from_text("Date: 04/06/2024")
        assert result == "20240604"

        # Test YYYY/MM/DD format
        result = parse_date_from_text("Date: 2024/06/04")
        assert result == "20240604"

        # Test Month DD, YYYY format
        result = parse_date_from_text("Date: Jun 04, 2024")
        assert result == "20240604"

        # Test no date found
        result = parse_date_from_text("No date here")
        assert result is None

    def test_extract_date_from_study_id(self, downloader):
        """Test extracting date from study ID using module-level function."""
        # Test YYYYMMDD format
        result = extract_date_from_study_id("study_20240604_abc123")
        assert result == "20240604"

        # Test YYYY-MM-DD format
        result = extract_date_from_study_id("study_2024-06-04_abc123")
        assert result == "20240604"

        # Test no date pattern
        result = extract_date_from_study_id("study_abc123")
        assert result is None

        # Test invalid date
        result = extract_date_from_study_id("study_20241301_abc123")  # Invalid month
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
    def test_download_pdf_success(self, mock_get, downloader, mock_study_info, temp_dir):
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
        mock_pdf_info = PDFDownloadInfo(
            url="https://test.com/test.pdf",
            text="Test PDF",
            study_url="https://wellbin.co/study/123",
            study_type="FhirStudy",
            study_date="20240604",
        )
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

    # Tests for bug fixes
    def test_is_valid_date(self, downloader):
        """Test date validation helper."""
        # Valid dates
        assert is_valid_date(2024, 6, 4) is True
        assert is_valid_date(2024, 2, 29) is True  # Leap year
        assert is_valid_date(2000, 2, 29) is True  # Leap year
        assert is_valid_date(2023, 12, 31) is True

        # Invalid dates
        assert is_valid_date(2023, 2, 29) is False  # Not a leap year
        assert is_valid_date(2024, 2, 30) is False  # February has 29 days max
        assert is_valid_date(2024, 4, 31) is False  # April has 30 days
        assert is_valid_date(2024, 13, 1) is False  # Invalid month
        assert is_valid_date(2024, 0, 1) is False  # Invalid month
        assert is_valid_date(2024, 1, 0) is False  # Invalid day
        assert is_valid_date(2024, 1, 32) is False  # Invalid day
        assert is_valid_date(1899, 6, 4) is False  # Year too old
        assert is_valid_date(2099, 6, 4) is True  # Year within range
        assert is_valid_date(2100, 6, 4) is False  # Year too new (limit is 2099)

    def test_sanitize_xpath_string(self, downloader):
        """Test XPath string sanitization."""
        # Test single quotes - should wrap in double quotes
        result = downloader._sanitize_xpath_string("test'value")
        assert result == '"test\'value"'

        # Test double quotes - should wrap in single quotes
        result = downloader._sanitize_xpath_string('test"value')
        assert result == "'test\"value'"

        # Test no quotes - should wrap in single quotes
        result = downloader._sanitize_xpath_string("testvalue")
        assert result == "'testvalue'"

        # Test both single and double quotes - should use concat()
        result = downloader._sanitize_xpath_string("test'value\"mixed")
        assert "concat" in result

        # Test special characters (should be preserved)
        result = downloader._sanitize_xpath_string("test/value?param=1")
        assert "test/value?param=1" in result

    def test_parse_date_invalid_dates_rejected(self, downloader):
        """Test that invalid dates are rejected even if pattern matches."""
        # Feb 30 should be rejected
        result = parse_date_from_text("Date: 30/02/2024")
        assert result is None

        # April 31 should be rejected
        result = parse_date_from_text("Date: 31/04/2024")
        assert result is None

        # Test with month 13 - second part > 12, so it will be parsed as MM/DD
        # 05/13/2024 -> 05 (month) / 13 (day) - valid, should return 20240513
        result = parse_date_from_text("Date: 05/13/2024")
        assert result == "20240513"  # 05 (month) / 13 (day) is valid

        # Valid Feb 29 in leap year should be accepted
        result = parse_date_from_text("Date: 29/02/2024")
        assert result == "20240229"

        # Invalid Feb 29 in non-leap year should be rejected
        result = parse_date_from_text("Date: 29/02/2023")
        assert result is None

    def test_extract_date_from_study_id_with_validation(self, downloader):
        """Test date extraction from study ID with proper validation."""
        # Valid date
        result = extract_date_from_study_id("study_20240604_abc123")
        assert result == "20240604"

        # Invalid date (Feb 30)
        result = extract_date_from_study_id("study_20240230_abc123")
        assert result is None

        # Invalid date (month 13)
        result = extract_date_from_study_id("study_20241304_abc123")
        assert result is None

        # Valid leap year date
        result = extract_date_from_study_id("study_20240229_abc123")
        assert result == "20240229"

        # Invalid non-leap year Feb 29
        result = extract_date_from_study_id("study_20230229_abc123")
        assert result is None

    def test_parse_date_ambiguous_format(self, downloader):
        """Test date parsing with ambiguous DD/MM vs MM/DD format."""
        # Test ambiguous date (both parts ≤ 12)
        # Should assume DD/MM/YYYY (European format)
        result = parse_date_from_text("Date: 04/06/2024")
        assert result == "20240604"

        # Test unambiguous - second part > 12 (must be MM/DD)
        result = parse_date_from_text("Date: 06/15/2024")
        assert result == "20240615"

        # Test unambiguous - first part > 12 (must be DD/MM)
        result = parse_date_from_text("Date: 15/06/2024")
        assert result == "20240615"

    def test_scrape_studies_resource_cleanup(self, downloader):
        """Test that both driver and session are cleaned up."""
        mock_driver = Mock()
        mock_session = Mock()
        downloader.driver = mock_driver
        downloader.session = mock_session

        with patch.object(downloader, "login", return_value=False):
            downloader.scrape_studies()

        # Both should be closed
        mock_driver.quit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_scrape_studies_resource_cleanup_on_error(self, downloader):
        """Test that resources are cleaned up even if driver.quit() fails."""
        mock_driver = Mock()
        mock_driver.quit.side_effect = Exception("Driver quit failed")
        mock_session = Mock()

        downloader.driver = mock_driver
        downloader.session = mock_session

        with patch.object(downloader, "login", return_value=False):
            # Should not raise exception even if driver.quit() fails
            downloader.scrape_studies()

        # Session should still be closed despite driver error
        mock_session.close.assert_called_once()

    # High Priority Tests - Critical Login & Scraping Logic
    @patch("wellbin.core.scraper.webdriver.Chrome")
    def test_login_success(self, mock_chrome, downloader):
        """Test successful login flow with form filling and dashboard detection."""
        # Setup mock driver
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver.current_url = "https://wellbin.co/dashboard"

        # Mock form elements
        email_field = Mock()
        password_field = Mock()
        submit_button = Mock()

        mock_driver.find_element.side_effect = [
            email_field,
            password_field,
            submit_button,
        ]

        # Perform login
        result = downloader.login()

        # Verify result
        assert result is True
        assert downloader.driver == mock_driver

        # Verify form interactions
        email_field.clear.assert_called_once()
        email_field.send_keys.assert_called_once_with("test@example.com")
        password_field.clear.assert_called_once()
        password_field.send_keys.assert_called_once_with("testpassword")
        submit_button.click.assert_called_once()

    @patch("wellbin.core.scraper.webdriver.Chrome")
    def test_login_failure_wrong_url(self, mock_chrome, downloader):
        """Test login failure when dashboard URL is not reached."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Mock form elements
        email_field = Mock()
        password_field = Mock()
        submit_button = Mock()

        mock_driver.find_element.side_effect = [
            email_field,
            password_field,
            submit_button,
        ]

        # Simulate wrong redirect URL
        mock_driver.current_url = "https://wellbin.co/login"

        result = downloader.login()

        assert result is False

    @patch("wellbin.core.scraper.webdriver.Chrome")
    def test_login_failure_missing_element(self, mock_chrome, downloader):
        """Test login failure when form elements cannot be found."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Simulate element not found
        mock_driver.find_element.side_effect = NoSuchElementException("Element not found")

        result = downloader.login()

        assert result is False

    @patch("wellbin.core.scraper.webdriver.Chrome")
    def test_get_study_links_filtering_fhir(self, mock_chrome, downloader):
        """Test study link filtering for FhirStudy type."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        downloader.setup_driver()

        # Create mock links with different study types
        fhir_link = Mock()
        fhir_link.get_attribute.return_value = "https://wellbin.co/study/123?type=FhirStudy"

        dicom_link = Mock()
        dicom_link.get_attribute.return_value = "https://wellbin.co/study/456?type=DicomStudy"

        # Mock finding links
        mock_driver.find_elements.return_value = [fhir_link, dicom_link]

        # Test with FhirStudy filter
        downloader.study_types = ["FhirStudy"]
        links = downloader.get_study_links()

        # Should only get FhirStudy
        assert len(links) == 1
        assert "type=FhirStudy" in links[0]

    @patch("wellbin.core.scraper.webdriver.Chrome")
    def test_get_study_links_filtering_all_types(self, mock_chrome, downloader):
        """Test study link filtering with 'all' study types."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        downloader.setup_driver()

        # Create mock links with different study types
        fhir_link = Mock()
        fhir_link.get_attribute.return_value = "https://wellbin.co/study/123?type=FhirStudy"

        dicom_link = Mock()
        dicom_link.get_attribute.return_value = "https://wellbin.co/study/456?type=DicomStudy"

        mock_driver.find_elements.return_value = [fhir_link, dicom_link]

        # Test with 'all' filter
        downloader.study_types = ["all"]
        links = downloader.get_study_links()

        # Should get both
        assert len(links) == 2

    @patch("wellbin.core.scraper.webdriver.Chrome")
    def test_get_study_links_with_limit(self, mock_chrome, downloader):
        """Test study link limiting."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        downloader.setup_driver()

        # Create 10 mock links
        mock_links = []
        for i in range(10):
            link = Mock()
            link.get_attribute.return_value = f"https://wellbin.co/study/{i}?type=FhirStudy"
            mock_links.append(link)

        mock_driver.find_elements.return_value = mock_links

        # Set limit to 5
        downloader.limit_studies = 5
        links = downloader.get_study_links()

        # Should only get 5
        assert len(links) == 5

    @patch("wellbin.core.scraper.requests.Session.get")
    def test_download_pdf_http_400_error(self, mock_get, downloader, mock_study_info):
        """Test PDF download with 400 Bad Request error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response

        result = downloader.download_pdf(mock_study_info)

        assert result is None
        mock_get.assert_called_once()

    @patch("wellbin.core.scraper.requests.Session.get")
    def test_download_pdf_http_403_forbidden(self, mock_get, downloader, mock_study_info):
        """Test PDF download with 403 Forbidden error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        result = downloader.download_pdf(mock_study_info)

        assert result is None

    @patch("wellbin.core.scraper.requests.Session.get")
    def test_download_pdf_http_500_error(self, mock_get, downloader, mock_study_info):
        """Test PDF download with 500 Server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = downloader.download_pdf(mock_study_info)

        assert result is None

    @patch("wellbin.core.scraper.requests.Session.get")
    def test_download_pdf_connection_timeout(self, mock_get, downloader, mock_study_info):
        """Test PDF download with connection timeout."""
        import requests

        mock_get.side_effect = requests.Timeout("Connection timed out")

        result = downloader.download_pdf(mock_study_info)

        assert result is None

    @patch("wellbin.core.scraper.requests.Session.get")
    def test_download_pdf_connection_error(self, mock_get, downloader, mock_study_info):
        """Test PDF download with connection error."""
        import requests

        mock_get.side_effect = requests.ConnectionError("Failed to connect")

        result = downloader.download_pdf(mock_study_info)

        assert result is None

    @patch("wellbin.core.scraper.requests.Session.get")
    def test_download_pdf_file_saved_correctly(self, mock_get, downloader, mock_study_info, temp_dir):
        """Test that downloaded PDF file is saved correctly."""
        # Update output dir to temp
        downloader.output_dir = str(temp_dir)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2", b"chunk3"]
        mock_get.return_value = mock_response

        result = downloader.download_pdf(mock_study_info)

        assert result is not None
        assert result.endswith(".pdf")

        # Verify file was created
        from pathlib import Path

        pdf_path = Path(result)
        assert pdf_path.exists()
        assert pdf_path.read_bytes() == b"chunk1chunk2chunk3"
