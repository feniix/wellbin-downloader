"""Tests for PDFDownloadManager class.

TDD RED phase: Define the interface and expected behavior before implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

from wellbin.core.exceptions import ConnectionTimeoutError, DownloadError, S3UrlExpiredError

if TYPE_CHECKING:
    from wellbin.core.download_manager import PDFDownloadManager


@pytest.mark.unit
class TestPDFDownloadManager:
    """Tests for PDFDownloadManager class."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> PDFDownloadManager:
        """Create a PDFDownloadManager instance for testing."""
        # Import here to avoid import errors during RED phase
        from wellbin.core.download_manager import PDFDownloadManager

        output = Mock()
        output.debug = Mock()
        output.progress = Mock()
        output.error = Mock()

        return PDFDownloadManager(
            output_dir=tmp_path,
            output=output,
            max_retries=3,
            chunk_size=8192,
        )

    def test_initialization(self, tmp_path: Path) -> None:
        """Test PDFDownloadManager initializes correctly."""
        from wellbin.core.download_manager import PDFDownloadManager

        output = Mock()
        manager = PDFDownloadManager(
            output_dir=tmp_path,
            output=output,
        )

        assert manager.output_dir == tmp_path
        assert manager.max_retries == 3  # default
        assert manager.chunk_size == 8192  # default

    def test_generate_filename_basic(self, manager: PDFDownloadManager) -> None:
        """Test filename generation with basic inputs."""
        result = manager.generate_filename(
            study_type="lab",
            study_date="20240315",
            counter=0,
        )
        assert result == "20240315-lab-0.pdf"

    def test_generate_filename_increments_counter(self, manager: PDFDownloadManager) -> None:
        """Test that counter increments correctly."""
        result = manager.generate_filename(
            study_type="imaging",
            study_date="20240315",
            counter=5,
        )
        assert result == "20240315-imaging-5.pdf"

    def test_generate_filename_unknown_date(self, manager: PDFDownloadManager) -> None:
        """Test filename with unknown date fallback."""
        result = manager.generate_filename(
            study_type="lab",
            study_date="unknown",
            counter=0,
        )
        assert result == "unknown-lab-0.pdf"

    @patch("requests.get")
    def test_download_pdf_success(self, mock_get: Mock, manager: PDFDownloadManager, tmp_path: Path) -> None:
        """Test successful PDF download."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content = Mock(return_value=[b"fake pdf content"])
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        file_path = tmp_path / "lab_reports" / "20240315-lab-0.pdf"

        result = manager.download_pdf(
            url="https://example.com/file.pdf",
            file_path=file_path,
        )

        assert result is True
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_download_pdf_http_error(self, mock_get: Mock, manager: PDFDownloadManager, tmp_path: Path) -> None:
        """Test PDF download with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        file_path = tmp_path / "lab_reports" / "20240315-lab-0.pdf"

        with pytest.raises(DownloadError):
            manager.download_pdf(
                url="https://example.com/notfound.pdf",
                file_path=file_path,
            )

    @patch("requests.get")
    def test_download_pdf_s3_expired(self, mock_get: Mock, manager: PDFDownloadManager, tmp_path: Path) -> None:
        """Test PDF download with expired S3 URL (403 Forbidden)."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        file_path = tmp_path / "lab_reports" / "20240315-lab-0.pdf"

        with pytest.raises(S3UrlExpiredError):
            manager.download_pdf(
                url="https://s3.amazonaws.com/expired-url",
                file_path=file_path,
            )

    @patch("requests.get")
    def test_download_pdf_connection_timeout(self, mock_get: Mock, manager: PDFDownloadManager, tmp_path: Path) -> None:
        """Test PDF download with connection timeout."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        file_path = tmp_path / "lab_reports" / "20240315-lab-0.pdf"

        with pytest.raises(ConnectionTimeoutError):
            manager.download_pdf(
                url="https://example.com/slow.pdf",
                file_path=file_path,
            )

    @patch("requests.get")
    def test_download_pdf_creates_directory(self, mock_get: Mock, manager: PDFDownloadManager, tmp_path: Path) -> None:
        """Test that download creates parent directory if needed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content = Mock(return_value=[b"content"])
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        # Use a subdirectory that doesn't exist
        file_path = tmp_path / "new_subdir" / "lab_reports" / "test.pdf"

        result = manager.download_pdf(
            url="https://example.com/file.pdf",
            file_path=file_path,
        )

        assert result is True
        assert file_path.parent.exists()

    def test_get_output_subdirectory_lab(self, manager: PDFDownloadManager, tmp_path: Path) -> None:
        """Test getting output subdirectory for lab reports."""
        result = manager.get_output_subdirectory("FhirStudy")
        assert result == tmp_path / "lab_reports"

    def test_get_output_subdirectory_imaging(self, manager: PDFDownloadManager, tmp_path: Path) -> None:
        """Test getting output subdirectory for imaging reports."""
        result = manager.get_output_subdirectory("DicomStudy")
        assert result == tmp_path / "imaging_reports"

    def test_get_output_subdirectory_unknown(self, manager: PDFDownloadManager, tmp_path: Path) -> None:
        """Test getting output subdirectory for unknown type."""
        result = manager.get_output_subdirectory("UnknownType")
        assert result == tmp_path / "other_reports"
