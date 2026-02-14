"""
Custom exception hierarchy for the Wellbin Medical Data Downloader.

This module provides a structured exception system for better error handling,
debugging, and user feedback throughout the application.
"""


class WellbinError(Exception):
    """Base exception for all Wellbin-related errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


# ============================================================================
# Authentication Errors
# ============================================================================


class AuthenticationError(WellbinError):
    """Base exception for authentication-related errors."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when provided credentials are invalid or malformed."""

    pass


class LoginFailedError(AuthenticationError):
    """Raised when login to the Wellbin platform fails."""

    pass


class SessionExpiredError(AuthenticationError):
    """Raised when the user session has expired during operation."""

    pass


# ============================================================================
# Network and Download Errors
# ============================================================================


class NetworkError(WellbinError):
    """Base exception for network-related errors."""

    pass


class DownloadError(NetworkError):
    """Base exception for download-related errors."""

    pass


class S3DownloadError(DownloadError):
    """Raised when downloading from S3 fails."""

    pass


class S3UrlExpiredError(S3DownloadError):
    """Raised when an S3 pre-signed URL has expired."""

    pass


class ConnectionTimeoutError(NetworkError):
    """Raised when a network connection times out."""

    pass


class MaxRetriesExceededError(NetworkError):
    """Raised when the maximum number of retries is exceeded."""

    pass


# ============================================================================
# Browser and Selenium Errors
# ============================================================================


class BrowserError(WellbinError):
    """Base exception for browser/Selenium-related errors."""

    pass


class BrowserSetupError(BrowserError):
    """Raised when browser initialization fails."""

    pass


class PageLoadError(BrowserError):
    """Raised when a page fails to load properly."""

    pass


class ElementNotFoundError(BrowserError):
    """Raised when a required page element cannot be found."""

    pass


class NavigationError(BrowserError):
    """Raised when navigation to a page fails."""

    pass


# ============================================================================
# Data Processing Errors
# ============================================================================


class DataProcessingError(WellbinError):
    """Base exception for data processing errors."""

    pass


class DateExtractionError(DataProcessingError):
    """Raised when date extraction from study data fails."""

    pass


class PDFProcessingError(DataProcessingError):
    """Raised when PDF processing or conversion fails."""

    pass


class InvalidStudyTypeError(DataProcessingError):
    """Raised when an invalid study type is specified."""

    pass


# ============================================================================
# Configuration Errors
# ============================================================================


class ConfigurationError(WellbinError):
    """Base exception for configuration-related errors."""

    pass


class MissingCredentialsError(ConfigurationError):
    """Raised when required credentials are not provided."""

    pass


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration values are invalid."""

    pass


# ============================================================================
# File System Errors
# ============================================================================


class FileSystemError(WellbinError):
    """Base exception for file system related errors."""

    pass


class DirectoryCreationError(FileSystemError):
    """Raised when directory creation fails."""

    pass


class FileWriteError(FileSystemError):
    """Raised when writing to a file fails."""

    pass
