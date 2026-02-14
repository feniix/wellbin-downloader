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

from .logging import Output, get_output


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
    def __init__(
        self,
        pdf_dir: str = "medical_data",
        output_dir: str = "markdown_reports",
        enhanced_mode: bool = False,
    ) -> None:
        """
        Initialize PDF to Markdown converter with enhanced PyMuPDF4LLM features

        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Directory to save markdown files
            enhanced_mode: Enable advanced features (page chunks, word positions, etc.)
        """
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.enhanced_mode = enhanced_mode
        self.out: Output = get_output()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
        return size >= 12 or "bold" in font

    def _is_subsection(self, text_upper: str, size: float) -> bool:
        """Check if text is a subsection header."""
        if not any(section in text_upper for section in self.SUBSECTIONS):
            return False
        return size >= 10

    @staticmethod
    def _is_parameter_header(text: str, size: float) -> bool:
        """Check if text is a parameter header (ends with colon)."""
        return text.endswith(":") and size >= 9

    def extract_enhanced_markdown(self, pdf_path: Path) -> str | list[PageChunk] | None:
        """Extract markdown with all advanced PyMuPDF4LLM features"""
        try:
            if self.enhanced_mode:
                # Enhanced extraction with page chunks and rich metadata (no images)
                return cast(
                    list[PageChunk],
                    pymupdf4llm.to_markdown(
                        str(pdf_path),
                        page_chunks=True,  # Rich page-by-page data
                        extract_words=True,  # Word-level extraction
                        ignore_images=True,  # Skip image processing entirely
                        table_strategy="lines",  # Aggressive table detection
                        hdr_info=self.medical_header_detector,  # Medical-specific headers
                        margins=10,  # Small margins for full content
                        show_progress=True,  # Show progress for large files
                    ),
                )
            else:
                # Simple extraction (current behavior)
                return cast(
                    str,
                    pymupdf4llm.to_markdown(str(pdf_path), hdr_info=self.medical_header_detector),
                )

        except Exception as e:
            self.out.error(f"Error extracting markdown from {pdf_path}: {e}")
            return None

    def save_enhanced_chunks(self, chunks: str | list[PageChunk], pdf_path: Path) -> list[Path]:
        """Save enhanced page chunks embedded in a single markdown file"""
        converted_files: list[Path] = []
        base_name = pdf_path.stem

        if isinstance(chunks, list):
            # Enhanced mode: embed all page chunks in one file
            output_filename = f"{base_name}.md"
            output_path = self.output_dir / output_filename

            # Build the complete document with embedded chunks
            content_parts: list[str] = []
            all_words: list[Any] = []

            # Document header with overall metadata
            total_pages = len(chunks)
            total_tables = sum(len(chunk.get("tables", [])) for chunk in chunks)

            # Collect all words for the footer
            for chunk in chunks:
                if "words" in chunk:
                    all_words.extend(chunk["words"])

            # Main document header
            header = f"""# Medical Report: {base_name}

**Source File:** `{base_name}.pdf`
**Extracted:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Processor:** PyMuPDF4LLM Enhanced Mode
**Optimized:** LLM medical data consumption
**Total Pages:** {total_pages}
**Tables Found:** {total_tables} tables detected
**Words Extracted:** {len(all_words)} words with positions

---

"""

            # Add each page as a section
            for i, chunk in enumerate(chunks):
                page_num = i + 1
                page_tables = chunk.get("tables", [])
                page_words = chunk.get("words", [])

                # Page section header
                page_header = f"""
## \U0001f4c4 Page {page_num}

**Page Number:** {page_num} of {total_pages}
**Tables on Page:** {len(page_tables)}
**Words on Page:** {len(page_words)}

"""

                # Page content
                page_content = chunk["text"]

                # Combine page section
                content_parts.append(page_header + page_content)

            # Combine all content
            full_content = header + "\n\n---\n\n".join(content_parts)

            # Add hidden footer with word data
            if all_words:
                footer = f"""

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
<summary>\U0001f4ca Word Position Data (Click to expand)</summary>

```json
{json.dumps(all_words, indent=2)}
```

</details>

<!-- End of word position data -->
"""
                full_content += footer

            # Save the complete document
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_content)

            converted_files.append(output_path)

        else:
            # Simple mode: single markdown file
            output_filename = base_name + ".md"
            output_path = self.output_dir / output_filename

            # Add simple header for non-enhanced mode
            header = f"""# Medical Report: {base_name}

**Source File:** `{base_name}.pdf`
**Extracted:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Processor:** PyMuPDF4LLM Standard Mode

---

"""

            final_markdown = header + chunks

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_markdown)

            converted_files.append(output_path)

        return converted_files

    def convert_pdf_to_markdown(self, pdf_path: Path) -> list[Path] | None:
        """Convert a single PDF to markdown using enhanced PyMuPDF4LLM features.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of created file paths, or None on failure
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

        except Exception as e:
            self.out.error(f"  Error converting {pdf_path.name}: {e}")
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
        self._print_batch_summary(result, pdf_files)

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

    def _print_batch_summary(self, result: ConversionResult, pdf_files: list[Path]) -> None:
        """Print batch conversion summary.

        Args:
            result: Conversion statistics
            pdf_files: Original list of PDF files
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
