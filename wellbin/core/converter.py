"""
PDF to Markdown Converter Core Module

Contains the PDFToMarkdownConverter class for converting medical PDFs
to markdown format optimized for LLM consumption.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, cast

import pymupdf4llm

from .exceptions import (
    FileWriteError,
    InvalidConfigurationError,
    PDFProcessingError,
)
from .logging import Output, get_output

# ============================================================================
# Configuration Constants
# ============================================================================

# Memory management thresholds
MAX_PDF_SIZE_MB = 100  # Warn for PDFs larger than 100MB
MAX_PAGES_ENHANCED_MODE = 50  # Limit for enhanced mode to prevent memory issues

# Header detection font size thresholds (in points)
MAIN_SECTION_MIN_SIZE = 12.0
SUBSECTION_MIN_SIZE = 10.0
PARAMETER_MIN_SIZE = 9.0

# Processing options
DEFAULT_TABLE_STRATEGY = "lines"
DEFAULT_MARGINS = 10


class PageChunk(TypedDict, total=False):
    """Structure returned by pymupdf4llm.to_markdown(page_chunks=True).

    Required keys are always present; optional keys depend on extraction settings.
    """

    text: str
    tables: list[dict[str, Any]]
    words: list[list[Any]]
    metadata: dict[str, Any]
    images: list[dict[str, Any]]
    toc_items: list[Any]


@dataclass
class ConversionStats:
    """Statistics about a PDF conversion."""

    pages_processed: int = 0
    tables_found: int = 0
    words_extracted: int = 0
    files_created: int = 0
    total_bytes: int = 0


@dataclass
class ConversionResult:
    """Result of a batch conversion operation."""

    successful: int = 0
    failed: int = 0
    total_files: int = 0
    total_bytes: int = 0
    failed_files: list[Path] = field(default_factory=list)
    successful_files: list[Path] = field(default_factory=list)


class PDFToMarkdownConverter:
    """PDF to Markdown converter with medical document optimization.

    Supports both standard and enhanced extraction modes with memory management
    safeguards for large documents.
    """

    def __init__(
        self,
        pdf_dir: str = "medical_data",
        output_dir: str = "markdown_reports",
        enhanced_mode: bool = False,
        max_pdf_size_mb: float = MAX_PDF_SIZE_MB,
        max_pages_enhanced: int = MAX_PAGES_ENHANCED_MODE,
    ) -> None:
        """
        Initialize PDF to Markdown converter with enhanced PyMuPDF4LLM features

        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Directory to save markdown files
            enhanced_mode: Enable advanced features (page chunks, word positions, etc.)
            max_pdf_size_mb: Maximum PDF size before warning (MB)
            max_pages_enhanced: Maximum pages for enhanced mode before warning

        Raises:
            InvalidConfigurationError: If directories cannot be created or accessed
        """
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.enhanced_mode = enhanced_mode
        self.max_pdf_size_mb = max_pdf_size_mb
        self.max_pages_enhanced = max_pages_enhanced
        self.out: Output = get_output()

        # Validate and create output directory
        self._validate_and_create_output_dir()

    # Class constants for medical header detection
    MAIN_SECTIONS: tuple[str, ...] = (
        # English terms
        "PATIENT INFORMATION",
        "LABORATORY RESULTS",
        "CLINICAL FINDINGS",
        "INTERPRETATION",
        "CONCLUSION",
        "RECOMMENDATION",
        "DIAGNOSIS",
        "LABORATORY DATA",
        "CHEMISTRY PANEL",
        "HEMATOLOGY",
        "IMAGING FINDINGS",
        "CLINICAL HISTORY",
        "EXAMINATION",
        "RESULTS",
        "FINDINGS",
        "IMPRESSION",
        "COMMENTS",
        # Spanish terms
        "HEMOGRAMA COMPLETO",
        "RESONANCIA MAGNETICA",
        "TIEMPO DE PROTROMBINA",
        "ERITROSEDIMENTACION",
        "FERRITINA",
        "APTT",
        "DIAGNOSTICO POR IMAGENES",
        "ESTUDIO",
    )

    SUBSECTIONS: tuple[str, ...] = (
        # English terms
        "CHEMISTRY",
        "HEMATOLOGY",
        "LIPID PANEL",
        "GLUCOSE",
        "ELECTROLYTES",
        "LIVER FUNCTION",
        "KIDNEY FUNCTION",
        "CARDIAC MARKERS",
        "TUMOR MARKERS",
        "HORMONES",
        "VITAMINS",
        "PROTEINS",
        "CBC",
        "DIFFERENTIAL",
        "PLATELET",
        "COAGULATION",
        # Spanish terms
        "SERIE ERITROCITARIA",
        "SERIE LEUCOCITARIA",
        "SERIE TROMBOCITARIA",
        "METODO",
        "CONCENTRACION",
    )

    def medical_header_detector(self, span: dict[str, Any], page: Any | None = None) -> str:
        """Custom header detection optimized for medical documents.

        Recognizes common medical report sections and subsections.

        Args:
            span: Text span dictionary with 'text', 'size', and 'font' keys
            page: Optional page object (unused but required by PyMuPDF4LLM)

        Returns:
            Markdown header prefix ('## ', '### ', '#### ', or '')
        """
        text = span.get("text", "").strip()
        size = span.get("size", 0)
        font = span.get("font", "").lower()
        text_upper = text.upper()

        # Check for main sections (H2)
        if self._is_main_section(text_upper, size, font):
            return "## "

        # Check for subsections (H3)
        if self._is_subsection(text_upper, size):
            return "### "

        # Parameter headers (H4)
        if self._is_parameter_header(text, size):
            return "#### "

        return ""

    def _is_main_section(self, text_upper: str, size: float, font: str) -> bool:
        """Check if text is a main medical section header."""
        if not any(section in text_upper for section in self.MAIN_SECTIONS):
            return False
        return size >= MAIN_SECTION_MIN_SIZE or "bold" in font

    def _is_subsection(self, text_upper: str, size: float) -> bool:
        """Check if text is a subsection header."""
        if not any(section in text_upper for section in self.SUBSECTIONS):
            return False
        return size >= SUBSECTION_MIN_SIZE

    @staticmethod
    def _is_parameter_header(text: str, size: float) -> bool:
        """Check if text is a parameter header (ends with colon)."""
        return text.endswith(":") and size >= PARAMETER_MIN_SIZE

    def _validate_and_create_output_dir(self) -> None:
        """Validate and create output directory with proper error handling.

        Raises:
            InvalidConfigurationError: If directory cannot be created or is not writable
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Verify directory is writable by attempting to create a test file
            test_file = self.output_dir / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except PermissionError as e:
                raise InvalidConfigurationError(
                    f"Output directory is not writable: {self.output_dir}",
                    details="Check directory permissions",
                ) from e

        except OSError as e:
            raise InvalidConfigurationError(
                f"Failed to create output directory: {self.output_dir}",
                details=str(e),
            ) from e

    def extract_enhanced_markdown(self, pdf_path: Path) -> str | list[PageChunk] | None:
        """Extract markdown with all advanced PyMuPDF4LLM features.

        Includes memory management safeguards for large PDFs.

        Args:
            pdf_path: Path to the PDF file to convert

        Returns:
            Markdown string (standard mode) or list of PageChunk dicts (enhanced mode),
            or None if extraction fails

        Raises:
            PDFProcessingError: If PDF file is corrupted or cannot be read
        """
        self._check_pdf_size(pdf_path)

        try:
            if self.enhanced_mode:
                return self._extract_enhanced_mode(pdf_path)
            else:
                return self._extract_standard_mode(pdf_path)

        except Exception as e:
            self.out.error(f"Error extracting markdown from {pdf_path}: {e}")
            return None

    def _check_pdf_size(self, pdf_path: Path) -> None:
        """Check PDF file size and warn if it exceeds thresholds.

        Args:
            pdf_path: Path to the PDF file to check
        """
        try:
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_pdf_size_mb:
                self.out.warning(
                    f"Large PDF detected ({file_size_mb:.1f}MB). Consider using standard mode for better memory usage."
                )
        except OSError:
            pass  # File doesn't exist or is inaccessible, let extraction fail naturally

    def _extract_enhanced_mode(self, pdf_path: Path) -> list[PageChunk]:
        """Extract PDF in enhanced mode with page chunks and rich metadata.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of PageChunk dictionaries with page-by-page data
        """
        return cast(
            list[PageChunk],
            pymupdf4llm.to_markdown(
                str(pdf_path),
                page_chunks=True,  # Rich page-by-page data
                extract_words=True,  # Word-level extraction
                ignore_images=True,  # Skip image processing entirely
                table_strategy=DEFAULT_TABLE_STRATEGY,
                hdr_info=self.medical_header_detector,
                margins=DEFAULT_MARGINS,
                show_progress=True,
            ),
        )

    def _extract_standard_mode(self, pdf_path: Path) -> str:
        """Extract PDF in standard mode (simple markdown).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Markdown string with document content
        """
        return cast(
            str,
            pymupdf4llm.to_markdown(str(pdf_path), hdr_info=self.medical_header_detector),
        )

    def save_enhanced_chunks(self, chunks: str | list[PageChunk], pdf_path: Path) -> list[Path]:
        """Save enhanced page chunks embedded in a single markdown file.

        Args:
            chunks: Either markdown string (standard) or list of PageChunk dicts (enhanced)
            pdf_path: Original PDF path for naming

        Returns:
            List of created file paths
        """
        base_name = pdf_path.stem
        output_path = self.output_dir / f"{base_name}.md"

        if isinstance(chunks, list):
            content = self._build_enhanced_document(chunks, base_name)
        else:
            content = self._build_standard_document(chunks, base_name)

        self._write_markdown_file(output_path, content)
        return [output_path]

    def _build_enhanced_document(self, chunks: list[PageChunk], base_name: str) -> str:
        """Build complete enhanced markdown document from page chunks.

        Args:
            chunks: List of PageChunk dictionaries
            base_name: Base filename for the document

        Returns:
            Complete markdown document string
        """
        # Collect metadata and word data
        all_words = self._collect_all_words(chunks)
        total_tables = sum(len(chunk.get("tables", [])) for chunk in chunks)

        # Build document header
        header = self._build_enhanced_header(base_name, len(chunks), total_tables, len(all_words))

        # Build page sections
        page_sections = self._build_page_sections(chunks, len(chunks))

        # Combine content
        full_content = header + "\n\n---\n\n".join(page_sections)

        # Add word position footer if available
        if all_words:
            full_content += self._build_word_footer(all_words)

        return full_content

    def _build_standard_document(self, markdown: str, base_name: str) -> str:
        """Build standard markdown document with header.

        Args:
            markdown: Raw markdown content
            base_name: Base filename for the document

        Returns:
            Complete markdown document string
        """
        header = f"""# Medical Report: {base_name}

**Source File:** `{base_name}.pdf`
**Extracted:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Processor:** PyMuPDF4LLM Standard Mode

---

"""
        return header + markdown

    def _collect_all_words(self, chunks: list[PageChunk]) -> list[Any]:
        """Collect all word data from page chunks.

        Args:
            chunks: List of PageChunk dictionaries

        Returns:
            Combined list of all word data
        """
        all_words: list[Any] = []
        for chunk in chunks:
            if "words" in chunk:
                all_words.extend(chunk["words"])
        return all_words

    def _build_enhanced_header(self, base_name: str, total_pages: int, total_tables: int, word_count: int) -> str:
        """Build enhanced document header with metadata.

        Args:
            base_name: Base filename
            total_pages: Number of pages in document
            total_tables: Number of tables found
            word_count: Total words extracted

        Returns:
            Header markdown string
        """
        return f"""# Medical Report: {base_name}

**Source File:** `{base_name}.pdf`
**Extracted:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Processor:** PyMuPDF4LLM Enhanced Mode
**Optimized:** LLM medical data consumption
**Total Pages:** {total_pages}
**Tables Found:** {total_tables} tables detected
**Words Extracted:** {word_count} words with positions

---

"""

    def _build_page_sections(self, chunks: list[PageChunk], total_pages: int) -> list[str]:
        """Build individual page section content.

        Args:
            chunks: List of PageChunk dictionaries
            total_pages: Total number of pages

        Returns:
            List of page section markdown strings
        """
        sections: list[str] = []
        for i, chunk in enumerate(chunks):
            page_num = i + 1
            page_tables = chunk.get("tables", [])
            page_words = chunk.get("words", [])

            page_header = f"""
## 📄 Page {page_num}

**Page Number:** {page_num} of {total_pages}
**Tables on Page:** {len(page_tables)}
**Words on Page:** {len(page_words)}

"""
            sections.append(page_header + chunk["text"])

        return sections

    def _build_word_footer(self, all_words: list[Any]) -> str:
        """Build hidden footer with word position data.

        Args:
            all_words: List of word position data

        Returns:
            Footer markdown string
        """
        return f"""

<!--
========================================
WORD POSITION DATA (HIDDEN SECTION)
========================================
This section contains word-level position data for programmatic analysis.
Format: [x0, y0, x1, y1, "word_text", block_num, line_num, word_num]
Coordinates are in PDF coordinate system.
Total words: {len(all_words)}
-->

<details>
<summary>📊 Word Position Data (Click to expand)</summary>

```json
{json.dumps(all_words, indent=2)}
```

</details>

<!-- End of word position data -->
"""

    def _write_markdown_file(self, output_path: Path, content: str) -> None:
        """Write markdown content to file with error handling.

        Args:
            output_path: Path to write the file
            content: Markdown content to write

        Raises:
            FileWriteError: If file cannot be written
        """
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        except PermissionError as e:
            raise FileWriteError(
                f"Permission denied writing to {output_path}",
                details="Check file permissions",
            ) from e
        except OSError as e:
            raise FileWriteError(
                f"Failed to write file {output_path}",
                details=str(e),
            ) from e

    def convert_pdf_to_markdown(self, pdf_path: Path) -> list[Path] | None:
        """Convert a single PDF to markdown using enhanced PyMuPDF4LLM features.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of created file paths, or None on failure

        Note:
            Custom exceptions (PDFProcessingError, FileWriteError) are caught and
            logged, returning None to allow batch processing to continue.
        """
        try:
            self._print_conversion_start(pdf_path)

            result = self.extract_enhanced_markdown(pdf_path)
            if not result:
                return None

            converted_files = self.save_enhanced_chunks(result, pdf_path)
            self._print_conversion_summary(converted_files)

            if self.enhanced_mode and isinstance(result, list):
                self._print_feature_stats(result)

            return converted_files

        except PDFProcessingError as e:
            self.out.error(f"  PDF processing error for {pdf_path.name}: {e.message}")
            if e.details:
                self.out.log("", f"    Details: {e.details}")
            return None
        except FileWriteError as e:
            self.out.error(f"  File write error for {pdf_path.name}: {e.message}")
            if e.details:
                self.out.log("", f"    Details: {e.details}")
            return None
        except Exception as e:
            self.out.error(f"  Unexpected error converting {pdf_path.name}: {e}")
            return None

    def _print_conversion_start(self, pdf_path: Path) -> None:
        """Print conversion start message."""
        self.out.log("\U0001f4c4", f"Converting {pdf_path.name}...")
        if self.enhanced_mode:
            self.out.action("  Enhanced mode: embedded page chunks + tables + word positions (no images)")

    def _print_conversion_summary(self, converted_files: list[Path]) -> None:
        """Print summary of converted files."""
        total_size = sum(f.stat().st_size for f in converted_files)
        self.out.success(f"  Saved {len(converted_files)} files ({total_size:,} bytes)")

    def _print_feature_stats(self, result: list[PageChunk]) -> None:
        """Print statistics about extracted features."""
        stats = self._calculate_feature_stats(result)

        self.out.progress(f"  Processed {stats.pages_processed} pages with rich metadata")

        if stats.tables_found > 0:
            self.out.log("\U0001f4cb", f"  Found {stats.tables_found} tables across all pages")
        if stats.words_extracted > 0:
            self.out.log("\U0001f4dd", f"  Extracted {stats.words_extracted} words with positions")

    def _calculate_feature_stats(self, result: list[PageChunk]) -> ConversionStats:
        """Calculate statistics from conversion result.

        Args:
            result: List of page chunk dictionaries

        Returns:
            ConversionStats with aggregated statistics
        """
        stats = ConversionStats(pages_processed=len(result))

        for chunk in result:
            stats.tables_found += len(chunk.get("tables", []))
            stats.words_extracted += len(chunk.get("words", []))

        return stats

    def convert_all_pdfs(self) -> list[Path]:
        """Convert all PDFs in the directory with enhanced features.

        Returns:
            List of all created file paths
        """
        pdf_files = self._find_pdf_files()
        if pdf_files is None:
            return []

        self._print_batch_start(pdf_files)

        result = self._process_all_pdfs(pdf_files)
        self._print_batch_summary(result)

        return result.successful_files

    def _find_pdf_files(self) -> list[Path] | None:
        """Find all PDF files in the directory.

        Returns:
            List of PDF paths, None if directory doesn't exist or is empty
        """
        if not self.pdf_dir.exists():
            self.out.error(f"PDF directory {self.pdf_dir} not found")
            return None

        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        if not pdf_files:
            self.out.error(f"No PDF files found in {self.pdf_dir}")
            return None

        return pdf_files

    def _print_batch_start(self, pdf_files: list[Path]) -> None:
        """Print batch conversion start information."""
        mode_desc = "Enhanced (embedded chunks + tables + words)" if self.enhanced_mode else "Standard"
        self.out.log("\U0001f504", f"Found {len(pdf_files)} PDF files to convert")
        self.out.action(f"Mode: {mode_desc}")
        self.out.log("\U0001f4c1", f"Output directory: {self.output_dir}")
        self.out.separator()

    def _process_all_pdfs(self, pdf_files: list[Path]) -> ConversionResult:
        """Process all PDF files and return results.

        Args:
            pdf_files: List of PDF paths to process

        Returns:
            ConversionResult with success/failure statistics
        """
        result = ConversionResult(total_files=len(pdf_files))
        successful_files: list[Path] = []

        for pdf_path in sorted(pdf_files):
            converted = self.convert_pdf_to_markdown(pdf_path)
            if converted:
                successful_files.extend(converted)
                result.successful += 1
            else:
                result.failed += 1
                result.failed_files.append(pdf_path)

        result.successful_files = successful_files
        result.total_bytes = sum(f.stat().st_size for f in successful_files) if successful_files else 0
        return result

    def _print_batch_summary(self, result: ConversionResult) -> None:
        """Print batch conversion summary.

        Args:
            result: Conversion statistics
        """
        self.out.header("\U0001f389 CONVERSION COMPLETE!")
        self.out.success(f"Successfully converted: {result.successful} PDFs")
        self.out.log("\U0001f4c4", f"Total markdown files: {len(result.successful_files)}")

        if result.failed > 0:
            self.out.error(f"Failed conversions: {result.failed} files")
            for failed in result.failed_files:
                self.out.log("", f"   - {failed.name}")

        if result.successful > 0:
            self._print_results_summary(result)

    def _print_results_summary(self, result: ConversionResult) -> None:
        """Print detailed results summary.

        Args:
            result: Conversion statistics
        """
        self.out.blank()
        self.out.progress("Results:")
        self.out.log("\U0001f4c1", f"   Output directory: {self.output_dir}")
        size_mb = result.total_bytes / 1024 / 1024
        self.out.log("\U0001f4be", f"   Total size: {result.total_bytes:,} bytes ({size_mb:.2f} MB)")

        if self.enhanced_mode:
            self.out.action("   Enhanced features: \u2713")
            self.out.log("\U0001f4d1", "   Page chunks: Embedded as sections in single files")
            self.out.progress("   Word positions: Embedded in footer sections")


def convert_structured_directories(
    input_dir: str, output_dir: str, file_type: str, enhanced_mode: bool = False
) -> list[Path]:
    """Convert PDFs from structured directories maintaining organization"""
    converted_files: list[Path] = []
    input_path = Path(input_dir)
    out = get_output()

    # Define subdirectory mappings
    type_mapping: dict[str, str] = {"lab_reports": "lab", "imaging_reports": "imaging"}

    for subdir in input_path.iterdir():
        if not subdir.is_dir():
            continue

        subdir_name = subdir.name
        report_type = type_mapping.get(subdir_name, "unknown")

        # Skip if file type filter doesn't match
        if file_type != "all" and file_type != report_type:
            out.log("\u23ed\ufe0f", f" Skipping {subdir_name}/ (filtered out)")
            continue

        out.log("\U0001f4c1", f"Processing {subdir_name}/...")

        # Create corresponding output subdirectory
        output_subdir = Path(output_dir) / f"{subdir_name}_markdown"
        output_subdir.mkdir(parents=True, exist_ok=True)

        # Convert PDFs in this subdirectory with enhanced mode
        converter = PDFToMarkdownConverter(str(subdir), str(output_subdir), enhanced_mode)
        subdir_files = converter.convert_all_pdfs()
        converted_files.extend(subdir_files)

        if subdir_files:
            out.success(f"  Converted {len(subdir_files)} files from {subdir_name}/")

    return converted_files
