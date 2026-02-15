"""Comprehensive tests for wellbin/core/exceptions.py.

This module tests all exception classes following TDD principles:
- Base class behavior (WellbinError)
- Simple subclass inheritance
- Complex subclasses with custom attributes
- String formatting and representation

Coverage target: 95%+ for exceptions.py
"""

from pathlib import Path

import pytest

from wellbin.core.exceptions import (
    AuthenticationError,
    BrowserError,
    BrowserSetupError,
    ConfigurationError,
    ConnectionTimeoutError,
    DataProcessingError,
    DateExtractionError,
    DirectoryCreationError,
    DownloadError,
    ElementNotFoundError,
    FileSystemError,
    FileWriteError,
    InvalidConfigurationError,
    InvalidCredentialsError,
    InvalidStudyTypeError,
    LoginFailedError,
    MaxRetriesExceededError,
    MissingCredentialsError,
    NavigationError,
    NetworkError,
    PageLoadError,
    PDFCorruptedError,
    PDFExtractionError,
    PDFProcessingError,
    PDFTooLargeError,
    S3DownloadError,
    S3UrlExpiredError,
    SessionExpiredError,
    WellbinError,
)


@pytest.mark.unit
class TestWellbinError:
    """Tests for the base WellbinError exception class."""

    def test_instantiation_with_message_only(self) -> None:
        """Test creating exception with just a message."""
        error = WellbinError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.details is None
        assert str(error) == "Something went wrong"

    def test_instantiation_with_message_and_details(self) -> None:
        """Test creating exception with message and details."""
        error = WellbinError("Auth failed", details="Invalid token format")
        assert error.message == "Auth failed"
        assert error.details == "Invalid token format"
        assert str(error) == "Auth failed - Details: Invalid token format"

    def test_inherits_from_exception(self) -> None:
        """Test that WellbinError inherits from Exception."""
        error = WellbinError("Test error")
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        """Test that exception can be raised and caught."""
        with pytest.raises(WellbinError) as exc_info:
            raise WellbinError("Test error")
        assert str(exc_info.value) == "Test error"

    def test_details_with_special_characters(self) -> None:
        """Test details with special characters and Unicode."""
        error = WellbinError("Error", details="Path: /tmp/ñoño.txt 🚨")
        assert "ñoño" in str(error)
        assert "🚨" in str(error)

    def test_empty_message(self) -> None:
        """Test with empty message string."""
        error = WellbinError("")
        assert error.message == ""
        assert str(error) == ""

    def test_multiline_message(self) -> None:
        """Test with multiline message."""
        error = WellbinError("Line 1\nLine 2", details="Multi\nline\ndetails")
        assert "\n" in error.message
        assert str(error).count("\n") == 3


@pytest.mark.unit
class TestAuthenticationExceptions:
    """Tests for authentication-related exception classes."""

    @pytest.mark.parametrize(
        "exception_class",
        [
            AuthenticationError,
            InvalidCredentialsError,
            LoginFailedError,
            SessionExpiredError,
        ],
    )
    def test_simple_authentication_exception_inheritance(self, exception_class: type[WellbinError]) -> None:
        """Test that authentication exceptions inherit from correct base."""
        error = exception_class("Test message")
        assert isinstance(error, WellbinError)
        assert isinstance(error, Exception)
        assert str(error) == "Test message"

    @pytest.mark.parametrize(
        "exception_class",
        [
            AuthenticationError,
            InvalidCredentialsError,
            LoginFailedError,
            SessionExpiredError,
        ],
    )
    def test_authentication_exception_with_details(self, exception_class: type[WellbinError]) -> None:
        """Test authentication exceptions with details."""
        error = exception_class("Auth error", details="Token expired")
        assert error.details == "Token expired"
        assert "Token expired" in str(error)


@pytest.mark.unit
class TestNetworkExceptions:
    """Tests for network-related exception classes."""

    @pytest.mark.parametrize(
        "exception_class",
        [
            NetworkError,
            DownloadError,
            S3DownloadError,
            S3UrlExpiredError,
            ConnectionTimeoutError,
            MaxRetriesExceededError,
        ],
    )
    def test_simple_network_exception_inheritance(self, exception_class: type[WellbinError]) -> None:
        """Test that network exceptions inherit from correct base."""
        error = exception_class("Network issue")
        assert isinstance(error, WellbinError)
        assert str(error) == "Network issue"

    def test_s3_url_expired_specific_use_case(self) -> None:
        """Test S3UrlExpiredError with realistic message."""
        error = S3UrlExpiredError(
            "S3 pre-signed URL has expired",
            details="URL generated at 2024-01-01T00:00:00Z",
        )
        assert "expired" in str(error).lower()

    def test_connection_timeout_with_url(self) -> None:
        """Test ConnectionTimeoutError with URL details."""
        error = ConnectionTimeoutError("Connection timed out", details="URL: https://wellbin.co/api")
        assert "timed out" in str(error).lower()


@pytest.mark.unit
class TestBrowserExceptions:
    """Tests for browser-related exception classes."""

    @pytest.mark.parametrize(
        "exception_class",
        [
            BrowserError,
            BrowserSetupError,
            PageLoadError,
            ElementNotFoundError,
            NavigationError,
        ],
    )
    def test_simple_browser_exception_inheritance(self, exception_class: type[WellbinError]) -> None:
        """Test that browser exceptions inherit from correct base."""
        error = exception_class("Browser issue")
        assert isinstance(error, WellbinError)
        assert str(error) == "Browser issue"

    def test_element_not_found_with_selector(self) -> None:
        """Test ElementNotFoundError with selector details."""
        error = ElementNotFoundError("Element not found", details="Selector: #login-button")
        assert "#login-button" in str(error)

    def test_page_load_error_with_url(self) -> None:
        """Test PageLoadError with URL details."""
        error = PageLoadError("Failed to load page", details="URL: https://wellbin.co/explorer")
        assert "wellbin.co" in str(error)


@pytest.mark.unit
class TestDataProcessingExceptions:
    """Tests for data processing exception classes."""

    @pytest.mark.parametrize(
        "exception_class",
        [DataProcessingError, DateExtractionError, InvalidStudyTypeError],
    )
    def test_simple_data_exception_inheritance(self, exception_class: type[WellbinError]) -> None:
        """Test that data processing exceptions inherit from correct base."""
        error = exception_class("Processing issue")
        assert isinstance(error, WellbinError)
        assert str(error) == "Processing issue"

    def test_date_extraction_error_with_context(self) -> None:
        """Test DateExtractionError with context details."""
        error = DateExtractionError("Could not extract date", details="Text: 'Report from unknown date'")
        assert "unknown date" in str(error)


@pytest.mark.unit
class TestPDFProcessingExceptions:
    """Tests for PDF-related exception classes."""

    def test_pdf_processing_error_basic(self) -> None:
        """Test PDFProcessingError with message only."""
        error = PDFProcessingError("PDF failed to process")
        assert error.message == "PDF failed to process"
        assert error.file_path is None
        assert str(error) == "PDF failed to process"

    def test_pdf_processing_error_with_file_path(self) -> None:
        """Test PDFProcessingError with file path."""
        error = PDFProcessingError("PDF corrupted", file_path=Path("/tmp/test.pdf"))
        assert error.file_path == Path("/tmp/test.pdf")
        assert "test.pdf" in str(error)

    def test_pdf_processing_error_with_all_params(self) -> None:
        """Test PDFProcessingError with all parameters."""
        error = PDFProcessingError(
            "PDF error",
            file_path=Path("/data/report.pdf"),
            details="Page 5 has invalid encoding",
        )
        assert error.file_path == Path("/data/report.pdf")
        assert "report.pdf" in str(error)
        assert "Page 5" in str(error)

    def test_pdf_too_large_error_basic(self) -> None:
        """Test PDFTooLargeError with message only."""
        error = PDFTooLargeError("PDF too large")
        assert error.message == "PDF too large"
        assert error.size_mb is None
        assert error.max_size_mb is None

    def test_pdf_too_large_error_with_sizes(self) -> None:
        """Test PDFTooLargeError with size information."""
        error = PDFTooLargeError(
            "PDF exceeds limit",
            file_path=Path("/tmp/huge.pdf"),
            size_mb=150.5,
            max_size_mb=100.0,
        )
        assert error.size_mb == 150.5
        assert error.max_size_mb == 100.0
        error_str = str(error)
        assert "150.5" in error_str
        assert "100.0" in error_str

    def test_pdf_too_large_error_partial_sizes(self) -> None:
        """Test PDFTooLargeError with only size_mb (no max)."""
        error = PDFTooLargeError(
            "Large PDF",
            size_mb=200.0,
        )
        assert error.size_mb == 200.0
        assert error.max_size_mb is None
        # Should not include size info in string if max not provided
        assert "200.0" not in str(error)

    @pytest.mark.parametrize(
        "exception_class",
        [PDFCorruptedError, PDFExtractionError],
    )
    def test_simple_pdf_exception_inheritance(self, exception_class: type[PDFProcessingError]) -> None:
        """Test that simple PDF exceptions inherit correctly."""
        error = exception_class("PDF issue")
        assert isinstance(error, PDFProcessingError)
        assert isinstance(error, DataProcessingError)
        assert isinstance(error, WellbinError)


@pytest.mark.unit
class TestConfigurationException:
    """Tests for configuration exception classes."""

    @pytest.mark.parametrize(
        "exception_class",
        [
            ConfigurationError,
            MissingCredentialsError,
            InvalidConfigurationError,
        ],
    )
    def test_simple_config_exception_inheritance(self, exception_class: type[WellbinError]) -> None:
        """Test that configuration exceptions inherit from correct base."""
        error = exception_class("Config issue")
        assert isinstance(error, WellbinError)
        assert str(error) == "Config issue"

    def test_missing_credentials_specific_message(self) -> None:
        """Test MissingCredentialsError with realistic message."""
        error = MissingCredentialsError(
            "Missing credentials",
            details="WELLBIN_EMAIL and WELLBIN_PASSWORD must be set",
        )
        assert "credentials" in str(error).lower()
        assert "WELLBIN_EMAIL" in str(error)


@pytest.mark.unit
class TestFileSystemExceptions:
    """Tests for file system exception classes."""

    @pytest.mark.parametrize(
        "exception_class",
        [FileSystemError, DirectoryCreationError, FileWriteError],
    )
    def test_simple_filesystem_exception_inheritance(self, exception_class: type[WellbinError]) -> None:
        """Test that filesystem exceptions inherit from correct base."""
        error = exception_class("Filesystem issue")
        assert isinstance(error, WellbinError)
        assert str(error) == "Filesystem issue"

    def test_directory_creation_error_with_path(self) -> None:
        """Test DirectoryCreationError with path details."""
        error = DirectoryCreationError(
            "Could not create directory",
            details="Path: /root/medical_data (Permission denied)",
        )
        assert "medical_data" in str(error)

    def test_file_write_error_with_path(self) -> None:
        """Test FileWriteError with path details."""
        error = FileWriteError(
            "Could not write file",
            details="Path: /tmp/report.pdf (Disk full)",
        )
        assert "report.pdf" in str(error)


@pytest.mark.unit
class TestExceptionChaining:
    """Tests for exception chaining and re-raising."""

    def test_exception_chaining_with_raise_from(self) -> None:
        """Test that exceptions can be chained."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise WellbinError("Wrapped error") from e
        except WellbinError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)

    def test_exception_context_implicit(self) -> None:
        """Test implicit exception context."""
        try:
            try:
                raise RuntimeError("Underlying issue")
            except RuntimeError as e:
                raise WellbinError("Higher level error") from e
        except WellbinError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, RuntimeError)


@pytest.mark.unit
class TestExceptionHierarchy:
    """Tests for the complete exception hierarchy."""

    def test_all_exceptions_inherit_from_wellbin_error(self) -> None:
        """Test that all custom exceptions inherit from WellbinError."""
        exception_classes = [
            AuthenticationError,
            InvalidCredentialsError,
            LoginFailedError,
            SessionExpiredError,
            NetworkError,
            DownloadError,
            S3DownloadError,
            S3UrlExpiredError,
            ConnectionTimeoutError,
            MaxRetriesExceededError,
            BrowserError,
            BrowserSetupError,
            PageLoadError,
            ElementNotFoundError,
            NavigationError,
            DataProcessingError,
            DateExtractionError,
            PDFProcessingError,
            PDFCorruptedError,
            PDFTooLargeError,
            PDFExtractionError,
            InvalidStudyTypeError,
            ConfigurationError,
            MissingCredentialsError,
            InvalidConfigurationError,
            FileSystemError,
            DirectoryCreationError,
            FileWriteError,
        ]
        for exc_class in exception_classes:
            assert issubclass(exc_class, WellbinError), f"{exc_class.__name__} should inherit from WellbinError"

    def test_s3_exceptions_hierarchy(self) -> None:
        """Test S3-specific exception hierarchy."""
        assert issubclass(S3UrlExpiredError, S3DownloadError)
        assert issubclass(S3DownloadError, DownloadError)
        assert issubclass(DownloadError, NetworkError)

    def test_pdf_exceptions_hierarchy(self) -> None:
        """Test PDF-specific exception hierarchy."""
        assert issubclass(PDFTooLargeError, PDFProcessingError)
        assert issubclass(PDFCorruptedError, PDFProcessingError)
        assert issubclass(PDFExtractionError, PDFProcessingError)
        assert issubclass(PDFProcessingError, DataProcessingError)

    def test_filesystem_exceptions_hierarchy(self) -> None:
        """Test filesystem exception hierarchy."""
        assert issubclass(DirectoryCreationError, FileSystemError)
        assert issubclass(FileWriteError, FileSystemError)
