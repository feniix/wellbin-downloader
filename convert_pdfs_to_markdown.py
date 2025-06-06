#!/usr/bin/env python3
"""
PDF to Markdown Converter for Medical Reports

Converts medical PDFs to markdown format optimized for LLM consumption.
Supports enhanced mode with page chunking, table detection, word-level extraction,
and medical-optimized header detection.

Enhanced mode provides:
- Page chunks embedded as sections in single markdown files
- Word position data in hidden expandable footers
- Table detection with position metadata
- Medical report header optimization
- Text-only processing (no images)
"""

import json
import os
from datetime import datetime
from pathlib import Path

import click
import pymupdf4llm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PDFToMarkdownConverter:
    def __init__(
        self, pdf_dir="medical_data", output_dir="markdown_reports", enhanced_mode=False
    ):
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

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def medical_header_detector(self, span, page=None):
        """
        Custom header detection optimized for medical documents

        Recognizes common medical report sections and subsections
        """
        text = span.get("text", "").strip()
        size = span.get("size", 0)
        font = span.get("font", "").lower()

        # Main medical report sections (H2)
        main_sections = [
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
        ]

        # Subsections (H3)
        subsections = [
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
        ]

        # Check for main sections
        if any(section in text.upper() for section in main_sections):
            if size >= 12 or "bold" in font:
                return "## "

        # Check for subsections
        if any(section in text.upper() for section in subsections):
            if size >= 10:
                return "### "

        # Parameter headers (H4)
        if text.endswith(":") and size >= 9:
            return "#### "

        return ""

    def extract_enhanced_markdown(self, pdf_path):
        """Extract markdown with all advanced PyMuPDF4LLM features"""
        try:
            if self.enhanced_mode:
                # Enhanced extraction with page chunks and rich metadata (no images)
                chunks = pymupdf4llm.to_markdown(
                    str(pdf_path),
                    page_chunks=True,  # Rich page-by-page data
                    extract_words=True,  # Word-level extraction
                    ignore_images=True,  # Skip image processing entirely
                    table_strategy="lines",  # Aggressive table detection
                    hdr_info=self.medical_header_detector,  # Medical-specific headers
                    margins=10,  # Small margins for full content
                    show_progress=True,  # Show progress for large files
                )
                return chunks
            else:
                # Simple extraction (current behavior)
                return pymupdf4llm.to_markdown(
                    str(pdf_path), hdr_info=self.medical_header_detector
                )

        except Exception as e:
            print(f"❌ Error extracting markdown from {pdf_path}: {e}")
            return None

    def save_enhanced_chunks(self, chunks, pdf_path):
        """Save enhanced page chunks embedded in a single markdown file"""
        converted_files = []
        base_name = pdf_path.stem

        if isinstance(chunks, list):
            # Enhanced mode: embed all page chunks in one file
            output_filename = f"{base_name}.md"
            output_path = self.output_dir / output_filename

            # Build the complete document with embedded chunks
            content_parts = []
            all_words = []

            # Document header with overall metadata
            doc_metadata = chunks[0].get("metadata", {}) if chunks else {}
            total_pages = len(chunks)
            total_tables = sum(len(chunk.get("tables", [])) for chunk in chunks)

            # Collect all words for the footer
            for chunk in chunks:
                if "words" in chunk:
                    all_words.extend(chunk["words"])

            # Main document header
            header = f"""# Medical Report: {base_name}

**Source File:** `{base_name}.pdf`
**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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
                page_metadata = chunk.get("metadata", {})
                page_tables = chunk.get("tables", [])
                page_words = chunk.get("words", [])

                # Page section header
                page_header = f"""
## 📄 Page {page_num}

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
<summary>📊 Word Position Data (Click to expand)</summary>

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
**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Processor:** PyMuPDF4LLM Standard Mode

---

"""

            final_markdown = header + chunks

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_markdown)

            converted_files.append(output_path)

        return converted_files

    def convert_pdf_to_markdown(self, pdf_path):
        """Convert a single PDF to markdown using enhanced PyMuPDF4LLM features"""
        try:
            print(f"📄 Converting {pdf_path.name}...")
            if self.enhanced_mode:
                print(
                    f"  🎯 Enhanced mode: embedded page chunks + tables + word positions (no images)"
                )

            # Extract markdown with advanced features
            result = self.extract_enhanced_markdown(pdf_path)
            if not result:
                return None

            # Save with appropriate format
            converted_files = self.save_enhanced_chunks(result, pdf_path)

            # Show results
            total_size = sum(f.stat().st_size for f in converted_files)
            print(f"  ✅ Saved {len(converted_files)} files ({total_size:,} bytes)")

            if self.enhanced_mode and isinstance(result, list):
                print(
                    f"  📊 Processed {len(result)} pages with rich metadata (embedded in single file)"
                )

                # Show detected features (no images)
                total_tables = sum(len(chunk.get("tables", [])) for chunk in result)
                total_words = sum(len(chunk.get("words", [])) for chunk in result)

                if total_tables > 0:
                    print(f"  📋 Found {total_tables} tables across all pages")
                if total_words > 0:
                    print(
                        f"  📝 Extracted {total_words} words with positions (embedded in footer)"
                    )

            return converted_files

        except Exception as e:
            print(f"  ❌ Error converting {pdf_path.name}: {e}")
            return None

    def convert_all_pdfs(self):
        """Convert all PDFs in the directory with enhanced features"""
        if not self.pdf_dir.exists():
            print(f"❌ PDF directory {self.pdf_dir} not found")
            return []

        # Find all PDF files
        pdf_files = list(self.pdf_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"❌ No PDF files found in {self.pdf_dir}")
            return []

        mode_desc = (
            "Enhanced (embedded chunks + tables + words)"
            if self.enhanced_mode
            else "Standard"
        )
        print(f"🔄 Found {len(pdf_files)} PDF files to convert")
        print(f"🎯 Mode: {mode_desc}")
        print(f"📁 Output directory: {self.output_dir}")
        print("=" * 60)

        all_converted_files = []
        failed_conversions = []

        for pdf_path in sorted(pdf_files):
            result = self.convert_pdf_to_markdown(pdf_path)
            if result:
                all_converted_files.extend(result)
            else:
                failed_conversions.append(pdf_path)

        # Summary
        print("\n" + "=" * 60)
        print("🎉 CONVERSION COMPLETE!")
        print("=" * 60)
        print(
            f"✅ Successfully converted: {len(pdf_files) - len(failed_conversions)} PDFs"
        )
        print(f"📄 Total markdown files: {len(all_converted_files)}")

        if failed_conversions:
            print(f"❌ Failed conversions: {len(failed_conversions)} files")
            for failed in failed_conversions:
                print(f"   - {failed.name}")

        if all_converted_files:
            total_size = sum(f.stat().st_size for f in all_converted_files)
            print(f"\n📊 Results:")
            print(f"   📁 Output directory: {self.output_dir}")
            print(
                f"   💾 Total size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)"
            )

            if self.enhanced_mode:
                print(f"   🎯 Enhanced features: ✓")
                print(f"   📑 Page chunks: Embedded as sections in single files")
                print(f"   📊 Word positions: Embedded in footer sections")

        return all_converted_files


def get_env_or_default(env_var, default_value, convert_type=None):
    """
    Get value from environment variable with proper fallback handling.

    Args:
        env_var: Environment variable name
        default_value: Default value if env var is empty or not set
        convert_type: Type conversion function (int, bool, etc.)

    Returns:
        Environment variable value or default, with proper type conversion
    """
    value = os.getenv(env_var, "").strip()

    # Use default if environment variable is empty or not set
    if not value:
        result = default_value
    else:
        result = value

    # Apply type conversion
    if convert_type == int:
        return int(result)
    elif convert_type == bool:
        if isinstance(result, bool):
            return result
        return str(result).lower() in ("true", "1", "yes", "on")

    return result


@click.command()
@click.option(
    "--input-dir",
    "-i",
    help="Input directory containing PDF files (overrides DEFAULT_INPUT_DIR env var)",
)
@click.option(
    "--output-dir",
    "-o",
    help="Output directory for markdown files (overrides DEFAULT_MARKDOWN_DIR env var)",
)
@click.option(
    "--preserve-structure",
    is_flag=True,
    help="Preserve subdirectory structure from input (overrides DEFAULT_PRESERVE_STRUCTURE env var)",
)
@click.option(
    "--file-type",
    "-t",
    type=click.Choice(["lab", "imaging", "all"]),
    help="Type of medical files to convert (overrides DEFAULT_FILE_TYPE env var)",
)
@click.option(
    "--enhanced-mode",
    is_flag=True,
    help="Enable enhanced mode with page chunks, tables, and word positions (overrides DEFAULT_ENHANCED_MODE env var)",
)
def main(input_dir, output_dir, preserve_structure, file_type, enhanced_mode):
    """
    PDF to Markdown Converter for Medical Reports

    Converts medical PDFs to markdown format optimized for LLM consumption.
    Supports both lab reports and medical imaging reports with proper categorization.

    Enhanced mode provides advanced features: page chunking, table detection,
    word-level extraction, and medical-optimized header detection (no images).

    ARGUMENT PRECEDENCE (highest to lowest):
    1. Command line arguments (--input-dir, --enhanced-mode, etc.)
    2. Environment variables (DEFAULT_INPUT_DIR, DEFAULT_ENHANCED_MODE, etc.)
    3. Built-in defaults

    Examples:
    \b
        # Basic conversion with defaults
        uv run python convert_pdfs_to_markdown.py

        # Enhanced mode (overrides any env var setting)
        uv run python convert_pdfs_to_markdown.py --enhanced-mode

        # Override env vars with specific directories
        uv run python convert_pdfs_to_markdown.py --input-dir my_pdfs --output-dir my_output --enhanced-mode

        # Convert only lab reports with enhanced features
        uv run python convert_pdfs_to_markdown.py --file-type lab --enhanced-mode
    """

    # PROPER PRECEDENCE: CLI args override env vars override defaults
    # Only use environment variables when CLI argument is NOT provided

    final_input_dir = (
        input_dir
        if input_dir is not None
        else get_env_or_default("DEFAULT_INPUT_DIR", "medical_data")
    )
    final_output_dir = (
        output_dir
        if output_dir is not None
        else get_env_or_default("DEFAULT_MARKDOWN_DIR", "markdown_reports")
    )
    final_file_type = (
        file_type
        if file_type is not None
        else get_env_or_default("DEFAULT_FILE_TYPE", "all")
    )

    # For flags: True if flag is provided, otherwise check env var, otherwise False
    final_preserve_structure = (
        preserve_structure
        if preserve_structure
        else get_env_or_default("DEFAULT_PRESERVE_STRUCTURE", "true", bool)
    )
    final_enhanced_mode = (
        enhanced_mode
        if enhanced_mode
        else get_env_or_default("DEFAULT_ENHANCED_MODE", "false", bool)
    )

    click.echo("🔄 PDF to Markdown Converter for Medical Reports")
    click.echo("🤖 Optimized for LLM consumption using PyMuPDF4LLM")
    click.echo("=" * 60)

    click.echo(f"📂 Input directory: {final_input_dir}")
    click.echo(f"📁 Output directory: {final_output_dir}")
    click.echo(f"🎯 File type filter: {final_file_type}")
    click.echo(f"🧠 Processing: LLM-optimized markdown extraction")

    if final_preserve_structure:
        click.echo("📁 Preserving subdirectory structure")
    if final_enhanced_mode:
        click.echo(
            "🎯 Enhanced mode: embedded page chunks + tables + word positions (no images)"
        )

    # Show precedence information
    click.echo("\n🔧 Argument Sources:")
    click.echo(f"   Input dir: {'CLI' if input_dir else 'ENV/Default'}")
    click.echo(f"   Output dir: {'CLI' if output_dir else 'ENV/Default'}")
    click.echo(f"   File type: {'CLI' if file_type else 'ENV/Default'}")
    click.echo(
        f"   Preserve structure: {'CLI' if preserve_structure else 'ENV/Default'}"
    )
    click.echo(f"   Enhanced mode: {'CLI' if enhanced_mode else 'ENV/Default'}")
    click.echo()

    # Handle structured vs flat directory conversion
    if final_preserve_structure and Path(final_input_dir).exists():
        converted_files = convert_structured_directories(
            final_input_dir, final_output_dir, final_file_type, final_enhanced_mode
        )
    else:
        # Create converter and run conversion on flat directory
        converter = PDFToMarkdownConverter(
            final_input_dir, final_output_dir, final_enhanced_mode
        )
        converted_files = converter.convert_all_pdfs()

    if converted_files:
        click.echo(f"\n💡 LLM Usage Examples:")
        click.echo(f"   📖 Read a report: cat {final_output_dir}/20250604-lab-0.md")
        click.echo(f"   🔍 Search all reports: grep -r 'keyword' {final_output_dir}/")
        click.echo(
            f"   📊 Count total reports: find {final_output_dir} -name '*.md' | wc -l"
        )
        click.echo(
            f"   🤖 Feed to LLM: cat {final_output_dir}/**/*.md | llm 'analyze trends'"
        )
        click.echo(
            f"   📈 Extract lab values: grep -h 'mg/dL\\|g/dL' {final_output_dir}/**/*.md"
        )
        click.echo(
            f"   🔬 Find abnormal: grep -i 'alto\\|bajo\\|high\\|low' {final_output_dir}/**/*.md"
        )

        if final_enhanced_mode:
            click.echo(f"\n🎯 Enhanced Mode Features:")
            click.echo(
                f"   📑 Page chunks: Embedded as sections in single markdown files"
            )
            click.echo(f"   📊 Word positions: Embedded in hidden footer sections")
            click.echo(f"   📋 Table detection: Built-in with position data")
            click.echo(f"   🧠 Medical headers: Optimized for lab/imaging reports")
            click.echo(f"   🚫 Images: Disabled (text-only processing)")


def convert_structured_directories(
    input_dir, output_dir, file_type, enhanced_mode=False
):
    """Convert PDFs from structured directories maintaining organization"""
    converted_files = []
    input_path = Path(input_dir)

    # Define subdirectory mappings
    type_mapping = {"lab_reports": "lab", "imaging_reports": "imaging"}

    for subdir in input_path.iterdir():
        if not subdir.is_dir():
            continue

        subdir_name = subdir.name
        report_type = type_mapping.get(subdir_name, "unknown")

        # Skip if file type filter doesn't match
        if file_type != "all" and file_type != report_type:
            click.echo(f"⏭️  Skipping {subdir_name}/ (filtered out)")
            continue

        click.echo(f"📁 Processing {subdir_name}/...")

        # Create corresponding output subdirectory
        output_subdir = Path(output_dir) / f"{subdir_name}_markdown"
        output_subdir.mkdir(parents=True, exist_ok=True)

        # Convert PDFs in this subdirectory with enhanced mode
        converter = PDFToMarkdownConverter(
            str(subdir), str(output_subdir), enhanced_mode
        )
        subdir_files = converter.convert_all_pdfs()
        converted_files.extend(subdir_files)

        if subdir_files:
            click.echo(f"  ✅ Converted {len(subdir_files)} files from {subdir_name}/")

    return converted_files


if __name__ == "__main__":
    main()
