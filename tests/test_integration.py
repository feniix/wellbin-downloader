"""
Integration tests using anonymized medical data fixtures.

These tests validate the entire conversion pipeline with realistic medical documents
based on real data but with anonymized personal information to ensure the converter
works correctly with medical terminology and structure.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from wellbin.core.converter import (
    PDFToMarkdownConverter,
    convert_structured_directories,
)

from .fixtures.medical_fixtures import (
    EXPECTED_PATTERNS,
    get_fixture_path,
    validate_fixture_content,
)


@pytest.mark.integration
class TestMedicalDataIntegration:
    """Integration tests using anonymized medical data fixtures."""

    def test_medical_fixtures_exist(self):
        """Test that medical data fixtures exist and are accessible."""
        # Test lab report fixtures
        lab_recent_path = get_fixture_path("lab", "recent")
        lab_older_path = get_fixture_path("lab", "older")

        assert lab_recent_path.exists(), f"Recent lab fixture should exist at {lab_recent_path}"
        assert lab_older_path.exists(), f"Older lab fixture should exist at {lab_older_path}"

        # Test imaging report fixtures
        imaging_recent_path = get_fixture_path("imaging", "recent")
        imaging_older_path = get_fixture_path("imaging", "older")

        assert imaging_recent_path.exists(), f"Recent imaging fixture should exist at {imaging_recent_path}"
        assert imaging_older_path.exists(), f"Older imaging fixture should exist at {imaging_older_path}"

    def test_fixture_content_validation(self, all_fixture_reports):
        """Test that fixture content contains valid medical report structures."""
        for report_name, content in all_fixture_reports.items():
            report_type = "lab" if "lab" in report_name else "imaging"

            # Validate content structure
            assert validate_fixture_content(report_type, content), f"Invalid content in {report_name}"

            # Check basic medical report structure
            assert "# Medical Report:" in content, f"Missing header in {report_name}"
            assert "**Source File:**" in content, f"Missing source file info in {report_name}"
            assert "**Extracted:**" in content, f"Missing extraction timestamp in {report_name}"

    def test_lab_report_content_structure(self, sample_lab_report_recent):
        """Test that lab reports contain expected medical terminology and structure."""
        content = sample_lab_report_recent

        # Check for lab-specific patterns
        EXPECTED_PATTERNS["lab"]

        # Should contain key lab report sections
        assert "HEMOGRAMA COMPLETO" in content, "Should have complete blood count section"
        assert "SERIE ERITROCITARIA" in content, "Should have red blood cell series"
        assert "SERIE LEUCOCITARIA" in content, "Should have white blood cell series"

        # Should contain measurements with units
        for unit in ["g/dl", "mg/dl", "%"]:
            assert unit in content, f"Should contain unit: {unit}"

        # Should contain medical parameters
        assert "Hemoglobina" in content, "Should contain hemoglobin measurement"
        assert "GLUCOSA" in content, "Should contain glucose measurement"

    def test_imaging_report_content_structure(self, sample_imaging_report_recent):
        """Test that imaging reports contain expected medical terminology and structure."""
        content = sample_imaging_report_recent

        # Check for imaging-specific patterns
        imaging_patterns = EXPECTED_PATTERNS["imaging"]

        # Should contain imaging study type
        assert any(header in content for header in ["RESONANCIA MAGNETICA", "TOMOGRAFIA COMPUTADA"]), (
            "Should contain imaging study type"
        )

        # Should contain findings section
        assert "HALLAZGOS" in content or "CONCLUSION" in content, "Should contain findings or conclusion section"

        # Should contain anatomical references
        anatomical_terms_found = sum(1 for term in imaging_patterns["anatomical_terms"] if term in content)
        assert anatomical_terms_found > 0, "Should contain anatomical terminology"

    def test_medical_header_detection_with_real_data(self):
        """Test header detection with patterns from real medical data."""
        temp_dir = Path("temp_test")
        temp_dir.mkdir(exist_ok=True)
        output_dir = temp_dir / "output"

        try:
            converter = PDFToMarkdownConverter(str(temp_dir), str(output_dir))

            # Test real patterns found in the medical data

            # From lab reports - main sections
            hemograma_span = {
                "text": "HEMOGRAMA COMPLETO",
                "size": 12,
                "font": "Arial-Bold",
            }
            assert converter.medical_header_detector(hemograma_span) == "## "

            # From imaging reports - main sections
            resonancia_span = {
                "text": "RESONANCIA MAGNETICA",
                "size": 14,
                "font": "Arial-Bold",
            }
            assert converter.medical_header_detector(resonancia_span) == "## "

            # Subsections from lab data
            serie_span = {"text": "SERIE ERITROCITARIA", "size": 11, "font": "Arial"}
            # This won't match as subsection because it's not in the predefined list
            # but it should not be a main section either
            result = converter.medical_header_detector(serie_span)
            assert result in ["", "### ", "#### "], f"Unexpected result: {result}"

            # Parameters with colons
            recuento_span = {
                "text": "Recuento de Glóbulos Rojos:",
                "size": 10,
                "font": "Arial",
            }
            # This should be H4 (parameter) since it ends with : and size >= 9
            assert converter.medical_header_detector(recuento_span) == "#### "

        finally:
            # Cleanup
            if output_dir.exists():
                for file in output_dir.iterdir():
                    file.unlink()
                output_dir.rmdir()
            if temp_dir.exists():
                temp_dir.rmdir()

    def test_filename_pattern_validation(self):
        """Test that fixture filenames match expected patterns."""
        # Test lab report patterns: YYYYMMDD-lab-N.md
        lab_recent_path = get_fixture_path("lab", "recent")
        lab_older_path = get_fixture_path("lab", "older")

        # Check filename patterns
        import re

        date_pattern = re.compile(r"^\d{8}-lab-\d+\.md$")

        assert date_pattern.match(lab_recent_path.name), (
            f"Lab recent filename should match pattern: {lab_recent_path.name}"
        )
        assert date_pattern.match(lab_older_path.name), (
            f"Lab older filename should match pattern: {lab_older_path.name}"
        )

        # Test imaging report patterns: YYYYMMDD-imaging-N.md
        imaging_recent_path = get_fixture_path("imaging", "recent")
        imaging_older_path = get_fixture_path("imaging", "older")

        imaging_pattern = re.compile(r"^\d{8}-imaging-\d+\.md$")

        assert imaging_pattern.match(imaging_recent_path.name), (
            f"Imaging recent filename should match pattern: {imaging_recent_path.name}"
        )
        assert imaging_pattern.match(imaging_older_path.name), (
            f"Imaging older filename should match pattern: {imaging_older_path.name}"
        )

    def test_converter_with_fixture_content(self, tmp_path, sample_lab_report_recent):
        """Test the converter using fixture content to simulate PDF conversion."""
        # Create test input directory with a mock PDF file
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        # Create a mock PDF file (just a placeholder)
        mock_pdf = input_dir / "20230615-lab-0.pdf"
        mock_pdf.write_bytes(b"%PDF-1.4 mock pdf content")

        # Test the converter
        converter = PDFToMarkdownConverter(str(input_dir), str(output_dir), enhanced_mode=False)

        # Mock pymupdf4llm to return our fixture content
        with patch("wellbin.core.converter.pymupdf4llm.to_markdown") as mock_to_md:
            # Return content similar to our fixtures but without the header (since that's added by the converter)
            fixture_lines = sample_lab_report_recent.split("\n")[7:]  # Skip the header part
            mock_content = "\n".join(fixture_lines)
            mock_to_md.return_value = mock_content

            result = converter.convert_all_pdfs()

            # Should have one converted file
            assert len(result) == 1
            assert result[0].exists()

            # Check content structure
            content = result[0].read_text()
            assert "# Medical Report:" in content
            assert "20230615-lab-0" in content
            assert "HEMOGRAMA COMPLETO" in content

    def test_structured_directories_with_fixture_layout(self, medical_fixtures_dir, tmp_path):
        """Test that structured conversion works with fixture directory layout."""
        # Create a structured input directory similar to the fixture layout
        input_dir = tmp_path / "input"
        lab_dir = input_dir / "lab_reports"
        imaging_dir = input_dir / "imaging_reports"

        lab_dir.mkdir(parents=True)
        imaging_dir.mkdir(parents=True)

        # Create mock PDF files based on fixture names
        lab_pdf1 = lab_dir / "20230615-lab-0.pdf"
        lab_pdf2 = lab_dir / "20180425-lab-1.pdf"
        imaging_pdf1 = imaging_dir / "20240318-imaging-0.pdf"
        imaging_pdf2 = imaging_dir / "20190815-imaging-1.pdf"

        for pdf_file in [lab_pdf1, lab_pdf2, imaging_pdf1, imaging_pdf2]:
            pdf_file.write_bytes(b"%PDF-1.4 mock pdf content")

        output_dir = tmp_path / "output"

        # Mock the actual conversion process
        with patch("wellbin.core.converter.PDFToMarkdownConverter") as mock_converter_class:
            mock_converter = mock_converter_class.return_value
            mock_converter.convert_all_pdfs.return_value = [Path("dummy.md")]

            # Test conversion with file type filter - only lab reports
            result = convert_structured_directories(
                str(input_dir),
                str(output_dir),
                "lab",  # Only lab reports
                enhanced_mode=False,
            )

            # Should have processed lab reports directory
            assert len(result) > 0, "Should have processed lab reports"
            mock_converter_class.assert_called()

            # Reset mock for imaging test
            mock_converter_class.reset_mock()

            # Test conversion with imaging reports
            result = convert_structured_directories(
                str(input_dir),
                str(output_dir),
                "imaging",  # Only imaging reports
                enhanced_mode=False,
            )

            # Should have processed imaging reports directory
            assert len(result) > 0, "Should have processed imaging reports"
            mock_converter_class.assert_called()
