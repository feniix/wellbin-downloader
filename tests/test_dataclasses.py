"""
Tests for wellbin dataclasses and structured data.
"""

from pathlib import Path

from wellbin.core.converter import ConversionResult, ConversionStats
from wellbin.core.scraper import DownloadResult, PDFDownloadInfo


class TestPDFDownloadInfo:
    """Tests for PDFDownloadInfo dataclass."""

    def test_pdf_download_info_creation(self):
        """Test creating a PDFDownloadInfo instance."""
        info = PDFDownloadInfo(
            url="https://example.com/test.pdf",
            text="Test PDF",
            study_url="https://wellbin.co/study/123?type=FhirStudy",
            study_type="FhirStudy",
            study_date="20240604",
        )

        assert info.url == "https://example.com/test.pdf"
        assert info.text == "Test PDF"
        assert info.study_url == "https://wellbin.co/study/123?type=FhirStudy"
        assert info.study_type == "FhirStudy"
        assert info.study_date == "20240604"
        assert info.study_index == 0  # default value

    def test_pdf_download_info_with_index(self):
        """Test creating PDFDownloadInfo with custom index."""
        info = PDFDownloadInfo(
            url="https://example.com/test.pdf",
            text="Test PDF",
            study_url="https://wellbin.co/study/123",
            study_type="DicomStudy",
            study_date="20240604",
            study_index=5,
        )

        assert info.study_index == 5

    def test_pdf_download_info_immutability(self):
        """Test that dataclass fields can be modified (default behavior)."""
        info = PDFDownloadInfo(
            url="https://example.com/test.pdf",
            text="Test PDF",
            study_url="https://wellbin.co/study/123",
            study_type="FhirStudy",
            study_date="20240604",
        )

        # Should be able to modify fields (not frozen)
        info.study_index = 10
        assert info.study_index == 10


class TestDownloadResult:
    """Tests for DownloadResult dataclass."""

    def test_download_result_creation(self):
        """Test creating a DownloadResult instance."""
        result = DownloadResult(
            local_path="/path/to/file.pdf",
            original_url="https://example.com/test.pdf",
            study_url="https://wellbin.co/study/123?type=FhirStudy",
            study_type="FhirStudy",
            study_date="20240604",
            description="Lab Report",
        )

        assert result.local_path == "/path/to/file.pdf"
        assert result.original_url == "https://example.com/test.pdf"
        assert result.study_url == "https://wellbin.co/study/123?type=FhirStudy"
        assert result.study_type == "FhirStudy"
        assert result.study_date == "20240604"
        assert result.description == "Lab Report"
        assert result.study_index == 0  # default value

    def test_download_result_with_index(self):
        """Test creating DownloadResult with custom index."""
        result = DownloadResult(
            local_path="/path/to/file.pdf",
            original_url="https://example.com/test.pdf",
            study_url="https://wellbin.co/study/123",
            study_type="DicomStudy",
            study_date="20240604",
            description="Imaging Report",
            study_index=3,
        )

        assert result.study_index == 3


class TestConversionStats:
    """Tests for ConversionStats dataclass."""

    def test_conversion_stats_defaults(self):
        """Test default values for ConversionStats."""
        stats = ConversionStats()

        assert stats.pages_processed == 0
        assert stats.tables_found == 0
        assert stats.words_extracted == 0
        assert stats.files_created == 0
        assert stats.total_bytes == 0

    def test_conversion_stats_custom_values(self):
        """Test creating ConversionStats with custom values."""
        stats = ConversionStats(
            pages_processed=10,
            tables_found=3,
            words_extracted=5000,
            files_created=5,
            total_bytes=1024000,
        )

        assert stats.pages_processed == 10
        assert stats.tables_found == 3
        assert stats.words_extracted == 5000
        assert stats.files_created == 5
        assert stats.total_bytes == 1024000

    def test_conversion_stats_mutation(self):
        """Test that stats can be updated incrementally."""
        stats = ConversionStats()

        stats.pages_processed += 5
        stats.tables_found += 2
        stats.words_extracted += 1000
        stats.files_created += 1
        stats.total_bytes += 50000

        assert stats.pages_processed == 5
        assert stats.tables_found == 2
        assert stats.words_extracted == 1000
        assert stats.files_created == 1
        assert stats.total_bytes == 50000


class TestConversionResult:
    """Tests for ConversionResult dataclass."""

    def test_conversion_result_defaults(self):
        """Test default values for ConversionResult."""
        result = ConversionResult()

        assert result.successful == 0
        assert result.failed == 0
        assert result.total_files == 0
        assert result.total_bytes == 0
        assert result.failed_files == []
        assert result.successful_files == []

    def test_conversion_result_custom_values(self):
        """Test creating ConversionResult with custom values."""
        successful_paths = [Path("/path/file1.md"), Path("/path/file2.md")]
        failed_paths = [Path("/path/bad.pdf")]

        result = ConversionResult(
            successful=2,
            failed=1,
            total_files=3,
            total_bytes=5000,
            failed_files=failed_paths,
            successful_files=successful_paths,
        )

        assert result.successful == 2
        assert result.failed == 1
        assert result.total_files == 3
        assert result.total_bytes == 5000
        assert result.failed_files == failed_paths
        assert result.successful_files == successful_paths

    def test_conversion_result_empty_lists(self):
        """Test that list fields default to empty lists."""
        result = ConversionResult()

        assert isinstance(result.failed_files, list)
        assert isinstance(result.successful_files, list)
        assert len(result.failed_files) == 0
        assert len(result.successful_files) == 0

    def test_conversion_result_list_mutation(self):
        """Test that list fields can be mutated."""
        result = ConversionResult()

        result.successful_files.append(Path("/path/file1.md"))
        result.failed_files.append(Path("/path/bad.pdf"))

        assert len(result.successful_files) == 1
        assert len(result.failed_files) == 1


class TestDataclassIntegration:
    """Integration tests for dataclass usage patterns."""

    def test_pdf_download_info_to_download_result_conversion(self):
        """Test pattern of converting PDFDownloadInfo to DownloadResult."""
        pdf_info = PDFDownloadInfo(
            url="https://example.com/test.pdf",
            text="Lab Report",
            study_url="https://wellbin.co/study/123?type=FhirStudy",
            study_type="FhirStudy",
            study_date="20240604",
            study_index=0,
        )

        # Simulate conversion to DownloadResult after successful download
        download_result = DownloadResult(
            local_path=f"/output/{pdf_info.study_date}-lab-{pdf_info.study_index}.pdf",
            original_url=pdf_info.url,
            study_url=pdf_info.study_url,
            study_type=pdf_info.study_type,
            study_date=pdf_info.study_date,
            description=pdf_info.text,
            study_index=pdf_info.study_index,
        )

        assert download_result.local_path == "/output/20240604-lab-0.pdf"
        assert download_result.original_url == pdf_info.url
        assert download_result.study_type == "FhirStudy"

    def test_conversion_stats_to_result_aggregation(self):
        """Test aggregating ConversionStats into ConversionResult."""
        # Simulate multiple file conversions
        all_stats = [
            ConversionStats(pages_processed=5, files_created=1, total_bytes=1000),
            ConversionStats(pages_processed=3, files_created=1, total_bytes=800),
            ConversionStats(pages_processed=8, files_created=1, total_bytes=2000),
        ]

        # Aggregate into result
        result = ConversionResult()
        for stats in all_stats:
            result.successful += stats.files_created
            result.total_files += stats.files_created
            result.total_bytes += stats.total_bytes

        assert result.successful == 3
        assert result.total_files == 3
        assert result.total_bytes == 3800
