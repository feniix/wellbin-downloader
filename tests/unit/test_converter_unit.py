"""Unit tests for wellbin/core/converter.py edge cases.

Focus on error handling paths and edge cases to improve coverage.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from wellbin.core.converter import (
    ConversionStats,
    PageChunk,
    PDFToMarkdownConverter,
)
from wellbin.core.exceptions import (
    FileWriteError,
    InvalidConfigurationError,
    PDFProcessingError,
)


@pytest.mark.unit
class TestConverterErrorHandling:
    """Tests for error handling paths in converter."""

    def test_output_dir_permission_error(self, tmp_path: Path) -> None:
        """Test _validate_and_create_output_dir handles PermissionError."""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")

            with patch("wellbin.core.converter.get_output") as mock_get_output:
                mock_get_output.return_value = Mock()

                with pytest.raises(InvalidConfigurationError) as exc_info:
                    PDFToMarkdownConverter(
                        pdf_dir=str(tmp_path),
                        output_dir=str(tmp_path / "output"),
                        enhanced_mode=False,
                    )

                # PermissionError is caught by OSError handler
                assert "Failed to create" in str(exc_info.value)

    def test_output_dir_os_error(self, tmp_path: Path) -> None:
        """Test _validate_and_create_output_dir handles OSError."""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = OSError("Disk full")

            with patch("wellbin.core.converter.get_output") as mock_get_output:
                mock_get_output.return_value = Mock()

                with pytest.raises(InvalidConfigurationError) as exc_info:
                    PDFToMarkdownConverter(
                        pdf_dir=str(tmp_path),
                        output_dir=str(tmp_path / "output"),
                        enhanced_mode=False,
                    )

                assert "Failed to create" in str(exc_info.value)


@pytest.mark.unit
class TestConverterPDFSizeCheck:
    """Tests for PDF size checking functionality."""

    @pytest.fixture
    def converter(self, tmp_path: Path) -> PDFToMarkdownConverter:
        """Create converter for testing with low threshold for testing."""
        return PDFToMarkdownConverter(
            pdf_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            enhanced_mode=False,
            max_pdf_size_mb=10,  # Set low threshold for testing
        )

    def test_check_pdf_size_large_file(self, converter: PDFToMarkdownConverter, tmp_path: Path) -> None:
        """Test _check_pdf_size warns for large files."""
        # Create a mock large PDF (20MB > 10MB threshold)
        large_pdf = tmp_path / "large.pdf"
        large_pdf.write_bytes(b"x" * (20 * 1024 * 1024))  # 20MB

        with patch.object(converter.out, "warning") as mock_warning:
            converter._check_pdf_size(large_pdf)
            mock_warning.assert_called_once()
            assert "Large PDF" in mock_warning.call_args[0][0]

    def test_check_pdf_size_normal_file(self, converter: PDFToMarkdownConverter, tmp_path: Path) -> None:
        """Test _check_pdf_size does not warn for normal files."""
        normal_pdf = tmp_path / "normal.pdf"
        normal_pdf.write_bytes(b"x" * (5 * 1024 * 1024))  # 5MB < 10MB threshold

        with patch.object(converter.out, "warning") as mock_warning:
            converter._check_pdf_size(normal_pdf)
            mock_warning.assert_not_called()

    def test_check_pdf_size_nonexistent_file(self, converter: PDFToMarkdownConverter, tmp_path: Path) -> None:
        """Test _check_pdf_size handles nonexistent files gracefully."""
        nonexistent = tmp_path / "nonexistent.pdf"

        # Should not raise
        converter._check_pdf_size(nonexistent)


@pytest.mark.unit
class TestConverterWriteMarkdown:
    """Tests for markdown file writing."""

    @pytest.fixture
    def converter(self, tmp_path: Path) -> PDFToMarkdownConverter:
        """Create converter for testing."""
        return PDFToMarkdownConverter(
            pdf_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            enhanced_mode=False,
        )

    def test_write_markdown_permission_error(self, converter: PDFToMarkdownConverter, tmp_path: Path) -> None:
        """Test _write_markdown_file handles PermissionError."""
        output_path = tmp_path / "output" / "test.md"

        with patch("builtins.open") as mock_open:
            mock_open.side_effect = PermissionError("Permission denied")

            with pytest.raises(FileWriteError) as exc_info:
                converter._write_markdown_file(output_path, "content")

            assert "Permission denied" in str(exc_info.value)

    def test_write_markdown_os_error(self, converter: PDFToMarkdownConverter, tmp_path: Path) -> None:
        """Test _write_markdown_file handles OSError."""
        output_path = tmp_path / "output" / "test.md"

        with patch("builtins.open") as mock_open:
            mock_open.side_effect = OSError("Disk full")

            with pytest.raises(FileWriteError) as exc_info:
                converter._write_markdown_file(output_path, "content")

            assert "Failed to write" in str(exc_info.value)


@pytest.mark.unit
class TestConverterPDFConversion:
    """Tests for PDF conversion error handling."""

    @pytest.fixture
    def converter(self, tmp_path: Path) -> PDFToMarkdownConverter:
        """Create converter for testing."""
        return PDFToMarkdownConverter(
            pdf_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            enhanced_mode=False,
        )

    def test_convert_pdf_to_markdown_pdf_error(self, converter: PDFToMarkdownConverter, tmp_path: Path) -> None:
        """Test convert_pdf_to_markdown handles PDFProcessingError."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        with patch.object(
            converter,
            "extract_enhanced_markdown",
            side_effect=PDFProcessingError("PDF corrupted"),
        ):
            with patch.object(converter.out, "error") as mock_error:
                result = converter.convert_pdf_to_markdown(pdf_path)
                assert result is None
                mock_error.assert_called()

    def test_convert_pdf_to_markdown_write_error(self, converter: PDFToMarkdownConverter, tmp_path: Path) -> None:
        """Test convert_pdf_to_markdown handles FileWriteError."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        with patch.object(
            converter,
            "extract_enhanced_markdown",
            return_value="markdown content",
        ):
            with patch.object(
                converter,
                "save_enhanced_chunks",
                side_effect=FileWriteError("Cannot write"),
            ):
                with patch.object(converter.out, "error") as mock_error:
                    result = converter.convert_pdf_to_markdown(pdf_path)
                    assert result is None
                    mock_error.assert_called()

    def test_convert_pdf_to_markdown_unexpected_error(self, converter: PDFToMarkdownConverter, tmp_path: Path) -> None:
        """Test convert_pdf_to_markdown handles unexpected errors."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        with patch.object(
            converter,
            "extract_enhanced_markdown",
            side_effect=RuntimeError("Unexpected"),
        ):
            with patch.object(converter.out, "error") as mock_error:
                result = converter.convert_pdf_to_markdown(pdf_path)
                assert result is None
                mock_error.assert_called()
                assert "Unexpected error" in mock_error.call_args[0][0]

    def test_convert_pdf_to_markdown_returns_none_on_empty_result(
        self, converter: PDFToMarkdownConverter, tmp_path: Path
    ) -> None:
        """Test convert_pdf_to_markdown returns None when extraction returns None."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        with patch.object(
            converter,
            "extract_enhanced_markdown",
            return_value=None,
        ):
            result = converter.convert_pdf_to_markdown(pdf_path)
            assert result is None


@pytest.mark.unit
class TestConverterFeatureStats:
    """Tests for feature statistics calculation."""

    @pytest.fixture
    def converter(self, tmp_path: Path) -> PDFToMarkdownConverter:
        """Create converter for testing."""
        return PDFToMarkdownConverter(
            pdf_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            enhanced_mode=True,
        )

    def test_calculate_feature_stats_basic(self, converter: PDFToMarkdownConverter) -> None:
        """Test basic feature stats calculation."""
        # PageChunk is a TypedDict, so create as dict
        chunks: list[PageChunk] = [
            {
                "text": "Page 1 content",
                "tables": [{"data": "table"}],
                "words": [["word1", 1, 2, 3, 4], ["word2", 5, 6, 7, 8]],
                "metadata": {"source": "test.pdf"},
            },
            {
                "text": "Page 2 content",
                "tables": [],
                "words": [["word3", 1, 2, 3, 4]],
                "metadata": {"source": "test.pdf"},
            },
        ]

        stats = converter._calculate_feature_stats(chunks)

        assert stats.pages_processed == 2
        assert stats.tables_found == 1
        assert stats.words_extracted == 3

    def test_calculate_feature_stats_empty(self, converter: PDFToMarkdownConverter) -> None:
        """Test feature stats with empty input."""
        stats = converter._calculate_feature_stats([])

        assert stats.pages_processed == 0
        assert stats.tables_found == 0
        assert stats.words_extracted == 0

    def test_print_feature_stats_with_tables(self, converter: PDFToMarkdownConverter) -> None:
        """Test printing feature stats with tables."""
        chunks: list[PageChunk] = [
            {
                "text": "content",
                "tables": [{"data": "table"}],
                "words": [],
                "metadata": {"source": "test.pdf"},
            },
        ]

        with patch.object(converter.out, "progress") as mock_progress:
            with patch.object(converter.out, "log") as mock_log:
                converter._print_feature_stats(chunks)
                # Should have called progress and log for tables
                mock_progress.assert_called_once()
                mock_log.assert_called()


@pytest.mark.unit
class TestConverterMedicalHeaderDetector:
    """Tests for medical header detection."""

    @pytest.fixture
    def converter(self, tmp_path: Path) -> PDFToMarkdownConverter:
        """Create converter for testing."""
        return PDFToMarkdownConverter(
            pdf_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            enhanced_mode=False,
        )

    @pytest.mark.parametrize(
        "text,size,expected",
        [
            ("PATIENT INFORMATION", 14, "## "),
            ("LABORATORY RESULTS", 14, "## "),
            ("CLINICAL FINDINGS", 14, "## "),
            ("HEMATOLOGY", 12, "## "),  # HEMATOLOGY is in MAIN_SECTIONS
            ("CHEMISTRY", 12, "### "),  # CHEMISTRY is in SUBSECTIONS
            ("Weight:", 10, "#### "),
            ("Blood Pressure:", 10, "#### "),
            ("Normal text", 10, ""),
            ("Small text", 8, ""),
        ],
        ids=[
            "main-section",
            "lab-results",
            "clinical",
            "hematology-main",
            "chemistry-sub",
            "weight-param",
            "bp-param",
            "normal-text",
            "small-text",
        ],
    )
    def test_header_detection(
        self,
        converter: PDFToMarkdownConverter,
        text: str,
        size: float,
        expected: str,
    ) -> None:
        """Test various header detection scenarios."""
        span = {"text": text, "size": size, "font": "Arial"}
        result = converter.medical_header_detector(span)
        assert result == expected

    def test_header_detection_case_insensitive(self, converter: PDFToMarkdownConverter) -> None:
        """Test header detection is case insensitive."""
        span_lower = {"text": "patient information", "size": 14, "font": "Arial"}
        span_upper = {"text": "PATIENT INFORMATION", "size": 14, "font": "Arial"}
        span_mixed = {"text": "Patient Information", "size": 14, "font": "Arial"}

        assert converter.medical_header_detector(span_lower) == "## "
        assert converter.medical_header_detector(span_upper) == "## "
        assert converter.medical_header_detector(span_mixed) == "## "


@pytest.mark.unit
class TestConversionStats:
    """Tests for ConversionStats dataclass."""

    def test_default_values(self) -> None:
        """Test default values of ConversionStats."""
        stats = ConversionStats()
        assert stats.pages_processed == 0
        assert stats.tables_found == 0
        assert stats.words_extracted == 0
        assert stats.files_created == 0
        assert stats.total_bytes == 0

    def test_custom_values(self) -> None:
        """Test custom values of ConversionStats."""
        stats = ConversionStats(
            pages_processed=10,
            tables_found=5,
            words_extracted=1000,
            files_created=2,
            total_bytes=50000,
        )
        assert stats.pages_processed == 10
        assert stats.tables_found == 5
        assert stats.words_extracted == 1000
        assert stats.files_created == 2
        assert stats.total_bytes == 50000
