"""
Tests for wellbin.core.converter module.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from wellbin.core.converter import (
    PDFToMarkdownConverter,
    convert_structured_directories,
)


class TestPDFToMarkdownConverter:
    """Tests for PDFToMarkdownConverter class."""

    def test_converter_initialization_standard_mode(self, temp_dir):
        """Test converter initialization in standard mode."""
        converter = PDFToMarkdownConverter(
            pdf_dir=str(temp_dir),
            output_dir=str(temp_dir / "output"),
            enhanced_mode=False,
        )

        assert converter.pdf_dir == Path(temp_dir)
        assert converter.output_dir == Path(temp_dir / "output")
        assert converter.enhanced_mode is False

    def test_converter_initialization_enhanced_mode(self, temp_dir):
        """Test converter initialization in enhanced mode."""
        converter = PDFToMarkdownConverter(
            pdf_dir=str(temp_dir),
            output_dir=str(temp_dir / "output"),
            enhanced_mode=True,
        )

        assert converter.enhanced_mode is True

    def test_output_directory_creation(self, temp_dir):
        """Test that output directory is created during initialization."""
        output_dir = temp_dir / "output"
        assert not output_dir.exists()

        PDFToMarkdownConverter(
            pdf_dir=str(temp_dir), output_dir=str(output_dir), enhanced_mode=False
        )

        assert output_dir.exists()

    def test_medical_header_detector(self, temp_dir):
        """Test medical header detection logic."""
        converter = PDFToMarkdownConverter(str(temp_dir), str(temp_dir / "output"))

        # Test main sections (H2)
        main_section_span = {
            "text": "LABORATORY RESULTS",
            "size": 14,
            "font": "Arial-Bold",
        }
        assert converter.medical_header_detector(main_section_span) == "## "

        # Test subsections (H3) - "CHEMISTRY" is in subsections list, size >= 10
        subsection_span = {"text": "CHEMISTRY", "size": 12, "font": "Arial"}
        assert converter.medical_header_detector(subsection_span) == "### "

        # Test parameter headers (H4) - ends with : and size >= 9, not in subsections
        parameter_span = {"text": "Weight:", "size": 10, "font": "Arial"}
        assert converter.medical_header_detector(parameter_span) == "#### "

        # Test conflict resolution - "CHEMISTRY:" should be subsection (H3) not parameter (H4)
        # because subsections are checked first
        conflict_span = {"text": "CHEMISTRY:", "size": 12, "font": "Arial"}
        assert converter.medical_header_detector(conflict_span) == "### "

        # Test no header
        normal_span = {"text": "Normal text", "size": 10, "font": "Arial"}
        assert converter.medical_header_detector(normal_span) == ""

    @patch("wellbin.core.converter.pymupdf4llm.to_markdown")
    def test_extract_enhanced_markdown_standard_mode(self, mock_to_markdown, temp_dir):
        """Test markdown extraction in standard mode."""
        mock_to_markdown.return_value = "# Test Markdown Content"

        converter = PDFToMarkdownConverter(
            str(temp_dir), str(temp_dir / "output"), enhanced_mode=False
        )
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")

        result = converter.extract_enhanced_markdown(pdf_path)

        assert result == "# Test Markdown Content"
        mock_to_markdown.assert_called_once()

    @patch("wellbin.core.converter.pymupdf4llm.to_markdown")
    def test_extract_enhanced_markdown_enhanced_mode(self, mock_to_markdown, temp_dir):
        """Test markdown extraction in enhanced mode."""
        mock_chunks = [
            {"text": "Page 1 content", "tables": [], "words": []},
            {"text": "Page 2 content", "tables": [], "words": []},
        ]
        mock_to_markdown.return_value = mock_chunks

        converter = PDFToMarkdownConverter(
            str(temp_dir), str(temp_dir / "output"), enhanced_mode=True
        )
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")

        result = converter.extract_enhanced_markdown(pdf_path)

        assert result == mock_chunks
        mock_to_markdown.assert_called_once_with(
            str(pdf_path),
            page_chunks=True,
            extract_words=True,
            ignore_images=True,
            table_strategy="lines",
            hdr_info=converter.medical_header_detector,
            margins=10,
            show_progress=True,
        )

    @patch("wellbin.core.converter.pymupdf4llm.to_markdown")
    def test_extract_enhanced_markdown_exception(self, mock_to_markdown, temp_dir):
        """Test handling of exceptions during markdown extraction."""
        mock_to_markdown.side_effect = Exception("PDF processing failed")

        converter = PDFToMarkdownConverter(str(temp_dir), str(temp_dir / "output"))
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")

        result = converter.extract_enhanced_markdown(pdf_path)

        assert result is None

    def test_save_enhanced_chunks_standard_mode(self, temp_dir):
        """Test saving chunks in standard mode."""
        converter = PDFToMarkdownConverter(str(temp_dir), str(temp_dir / "output"))
        pdf_path = temp_dir / "test.pdf"
        markdown_content = "# Test Content\n\nSample markdown"

        result = converter.save_enhanced_chunks(markdown_content, pdf_path)

        assert len(result) == 1
        assert result[0].name == "test.md"
        assert result[0].exists()

        content = result[0].read_text()
        assert "# Medical Report: test" in content
        assert "Sample markdown" in content

    def test_save_enhanced_chunks_enhanced_mode(self, temp_dir):
        """Test saving chunks in enhanced mode."""
        converter = PDFToMarkdownConverter(str(temp_dir), str(temp_dir / "output"))
        pdf_path = temp_dir / "test.pdf"

        chunks = [
            {"text": "Page 1 content", "tables": [], "words": []},
            {
                "text": "Page 2 content",
                "tables": [{"table": "data"}],
                "words": [{"word": "test"}],
            },
        ]

        result = converter.save_enhanced_chunks(chunks, pdf_path)

        assert len(result) == 1
        assert result[0].name == "test.md"
        assert result[0].exists()

        content = result[0].read_text()
        assert "# Medical Report: test" in content
        assert "## 📄 Page 1" in content
        assert "## 📄 Page 2" in content
        assert "Page 1 content" in content
        assert "Page 2 content" in content

    def test_convert_all_pdfs_no_files(self, temp_dir):
        """Test convert_all_pdfs with no PDF files."""
        converter = PDFToMarkdownConverter(str(temp_dir), str(temp_dir / "output"))

        result = converter.convert_all_pdfs()

        assert result == []

    def test_convert_all_pdfs_missing_directory(self, temp_dir):
        """Test convert_all_pdfs with missing input directory."""
        nonexistent_dir = temp_dir / "nonexistent"
        converter = PDFToMarkdownConverter(
            str(nonexistent_dir), str(temp_dir / "output")
        )

        result = converter.convert_all_pdfs()

        assert result == []

    @patch.object(PDFToMarkdownConverter, "convert_pdf_to_markdown")
    def test_convert_all_pdfs_with_files(self, mock_convert, temp_dir):
        """Test convert_all_pdfs with PDF files."""
        # Create sample PDF files
        pdf1 = temp_dir / "test1.pdf"
        pdf2 = temp_dir / "test2.pdf"
        pdf1.write_bytes(b"fake pdf 1")
        pdf2.write_bytes(b"fake pdf 2")

        # Create output directory and mock markdown files
        output_dir = temp_dir / "output"
        output_dir.mkdir(exist_ok=True)

        # Create the actual files that will be returned
        md1 = output_dir / "test1.md"
        md2 = output_dir / "test2.md"
        md1.write_text("# Test 1 markdown")
        md2.write_text("# Test 2 markdown")

        # Mock successful conversion to return the files we created
        def mock_conversion_side_effect(*args):
            return [md1] if "test1" in str(args[0]) else [md2]

        mock_convert.side_effect = mock_conversion_side_effect

        converter = PDFToMarkdownConverter(str(temp_dir), str(output_dir))
        result = converter.convert_all_pdfs()

        assert len(result) == 2  # Two successful conversions
        assert mock_convert.call_count == 2


class TestConvertStructuredDirectories:
    """Tests for convert_structured_directories function."""

    def test_convert_structured_directories_all_types(self, temp_dir):
        """Test converting all file types from structured directories."""
        # Create input structure
        input_dir = temp_dir / "input"
        lab_dir = input_dir / "lab_reports"
        imaging_dir = input_dir / "imaging_reports"
        lab_dir.mkdir(parents=True)
        imaging_dir.mkdir(parents=True)

        # Create sample PDFs
        (lab_dir / "test_lab.pdf").write_bytes(b"fake lab pdf")
        (imaging_dir / "test_imaging.pdf").write_bytes(b"fake imaging pdf")

        output_dir = temp_dir / "output"

        # Mock the converter
        with patch.object(PDFToMarkdownConverter, "convert_all_pdfs") as mock_convert:
            mock_convert.return_value = [Path("test.md")]

            result = convert_structured_directories(
                str(input_dir), str(output_dir), "all", enhanced_mode=True
            )

            assert len(result) == 2  # Both directories processed
            assert mock_convert.call_count == 2

    def test_convert_structured_directories_filtered(self, temp_dir):
        """Test converting with file type filter."""
        # Create input structure
        input_dir = temp_dir / "input"
        lab_dir = input_dir / "lab_reports"
        imaging_dir = input_dir / "imaging_reports"
        lab_dir.mkdir(parents=True)
        imaging_dir.mkdir(parents=True)

        output_dir = temp_dir / "output"

        # Mock the converter
        with patch.object(PDFToMarkdownConverter, "convert_all_pdfs") as mock_convert:
            mock_convert.return_value = [Path("test.md")]

            result = convert_structured_directories(
                str(input_dir),
                str(output_dir),
                "lab",  # Only lab reports
                enhanced_mode=False,
            )

            # Only lab_reports directory should be processed
            assert len(result) == 1
            assert mock_convert.call_count == 1

    def test_convert_structured_directories_no_subdirs(self, temp_dir):
        """Test converting with no matching subdirectories."""
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        output_dir = temp_dir / "output"

        result = convert_structured_directories(
            str(input_dir), str(output_dir), "all", enhanced_mode=False
        )

        assert result == []
