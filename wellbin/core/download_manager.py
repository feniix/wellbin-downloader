"""
PDF Download Manager for the Wellbin Medical Data Downloader.

This module provides a dedicated class for managing PDF downloads from S3 URLs,
including filename generation, retry logic, and error handling.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import requests

from wellbin.core.exceptions import (
    ConnectionTimeoutError,
    DownloadError,
    S3UrlExpiredError,
)

if TYPE_CHECKING:
    from wellbin.core.logging import Output


class PDFDownloadManager:
    """Manages PDF downloads from S3 URLs with retry logic and error handling.

    This class encapsulates all PDF download functionality, separating concerns
    from the main scraper class for better testability and maintainability.

    Attributes:
        output_dir: Base directory for downloaded files
        output: Output handler for logging and progress messages
        max_retries: Maximum number of download retry attempts
        chunk_size: Size of chunks for streaming downloads
    """

    # Mapping of study types to output subdirectories
    STUDY_TYPE_DIRS: dict[str, str] = {
        "FhirStudy": "lab_reports",
        "DicomStudy": "imaging_reports",
    }
    DEFAULT_SUBDIR = "other_reports"

    def __init__(
        self,
        output_dir: Path,
        output: "Output",
        max_retries: int = 3,
        chunk_size: int = 8192,
    ) -> None:
        """Initialize the PDFDownloadManager.

        Args:
            output_dir: Base directory for downloaded files
            output: Output handler for logging and progress
            max_retries: Maximum retry attempts (default: 3)
            chunk_size: Chunk size for streaming downloads (default: 8192)
        """
        self.output_dir = output_dir
        self.output = output
        self.max_retries = max_retries
        self.chunk_size = chunk_size

    def generate_filename(
        self,
        study_type: str,
        study_date: str,
        counter: int,
    ) -> str:
        """Generate a unique filename for a downloaded PDF.

        Args:
            study_type: Type of study (e.g., "lab", "imaging")
            study_date: Date string in YYYYMMDD format
            counter: Sequential counter for deduplication

        Returns:
            Filename in format: YYYYMMDD-{type}-{counter}.pdf
        """
        return f"{study_date}-{study_type}-{counter}.pdf"

    def get_output_subdirectory(self, study_type: str) -> Path:
        """Get the output subdirectory for a given study type.

        Args:
            study_type: The type of study (e.g., "FhirStudy", "DicomStudy")

        Returns:
            Path to the appropriate subdirectory
        """
        subdir_name = self.STUDY_TYPE_DIRS.get(study_type, self.DEFAULT_SUBDIR)
        return self.output_dir / subdir_name

    def download_pdf(
        self,
        url: str,
        file_path: Path,
    ) -> bool:
        """Download a PDF from a URL to a local file.

        Args:
            url: URL to download from (typically S3 pre-signed URL)
            file_path: Local path to save the file

        Returns:
            True if download was successful

        Raises:
            S3UrlExpiredError: If S3 URL returns 403 (expired)
            DownloadError: If download fails with HTTP error
            ConnectionTimeoutError: If connection times out
        """
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with requests.get(url, stream=True, timeout=30) as response:
                # Check for HTTP errors
                if response.status_code == 403:
                    raise S3UrlExpiredError(
                        "S3 pre-signed URL has expired",
                        details=f"URL: {url[:50]}...",
                    )

                if response.status_code != 200:
                    raise DownloadError(
                        f"HTTP {response.status_code}: {response.reason}",
                        details=f"URL: {url[:50]}...",
                    )

                # Stream download to file
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)

                self.output.debug(f"Successfully downloaded: {file_path.name}")
                return True

        except requests.exceptions.Timeout as e:
            self.output.error(f"Connection timeout: {e}")
            raise ConnectionTimeoutError(
                "Connection timed out during download",
                details=f"URL: {url[:50]}...",
            ) from e

        except requests.exceptions.ConnectionError as e:
            self.output.error(f"Connection error: {e}")
            raise DownloadError(
                "Failed to connect to server",
                details=str(e),
            ) from e
