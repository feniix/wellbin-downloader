"""
Convert command for converting PDFs to markdown format.
"""

import click
from dotenv import load_dotenv

from ..core.converter import PDFToMarkdownConverter, convert_structured_directories
from ..core.utils import get_env_or_default

# Load environment variables
load_dotenv()


@click.command()
@click.option(
    "--input-dir",
    "-i",
    help="Input directory containing PDF files (overrides WELLBIN_INPUT_DIR env var)",
)
@click.option(
    "--output-dir",
    "-o",
    help="Output directory for markdown files (overrides WELLBIN_MARKDOWN_DIR env var)",
)
@click.option(
    "--preserve-structure",
    is_flag=True,
    help="Preserve subdirectory structure from input (overrides WELLBIN_PRESERVE_STRUCTURE env var)",
)
@click.option(
    "--file-type",
    "-t",
    type=click.Choice(["lab", "imaging", "all"]),
    help="Type of medical files to convert (overrides WELLBIN_FILE_TYPE env var)",
)
@click.option(
    "--enhanced-mode",
    is_flag=True,
    help="Enable enhanced mode with page chunks, tables, and word positions (overrides WELLBIN_ENHANCED_MODE env var)",
)
def convert(input_dir, output_dir, preserve_structure, file_type, enhanced_mode):
    """
    Convert medical PDFs to markdown format optimized for LLM consumption.

    Supports both lab reports and medical imaging reports with proper categorization.
    Enhanced mode provides advanced features: page chunking, table detection,
    word-level extraction, and medical-optimized header detection (no images).

    ARGUMENT PRECEDENCE (highest to lowest):
    1. Command line arguments (--input-dir, --enhanced-mode, etc.)
    2. Environment variables (WELLBIN_INPUT_DIR, WELLBIN_ENHANCED_MODE, etc.)
    3. Built-in defaults

    Examples:
    \b
        # Basic conversion with defaults
        uv run wellbin convert

        # Enhanced mode (overrides any env var setting)
        uv run wellbin convert --enhanced-mode

        # Override env vars with specific directories
        uv run wellbin convert --input-dir my_pdfs --output-dir my_output --enhanced-mode

        # Convert only lab reports with enhanced features
        uv run wellbin convert --file-type lab --enhanced-mode
    """

    # PROPER PRECEDENCE: CLI args override env vars override defaults
    # Only use environment variables when CLI argument is NOT provided

    final_input_dir = (
        input_dir
        if input_dir is not None
        else get_env_or_default("WELLBIN_INPUT_DIR", "medical_data")
    )
    final_output_dir = (
        output_dir
        if output_dir is not None
        else get_env_or_default("WELLBIN_MARKDOWN_DIR", "markdown_reports")
    )
    final_file_type = (
        file_type
        if file_type is not None
        else get_env_or_default("WELLBIN_FILE_TYPE", "all")
    )

    # For flags: True if flag is provided, otherwise check env var, otherwise False
    final_preserve_structure = (
        preserve_structure
        if preserve_structure
        else get_env_or_default("WELLBIN_PRESERVE_STRUCTURE", "true", bool)
    )
    final_enhanced_mode = (
        enhanced_mode
        if enhanced_mode
        else get_env_or_default("WELLBIN_ENHANCED_MODE", "false", bool)
    )

    click.echo("🔄 PDF to Markdown Converter for Medical Reports")
    click.echo("🤖 Optimized for LLM consumption using PyMuPDF4LLM")
    click.echo("=" * 60)

    click.echo(f"📂 Input directory: {final_input_dir}")
    click.echo(f"📁 Output directory: {final_output_dir}")
    click.echo(f"🎯 File type filter: {final_file_type}")
    click.echo("🧠 Processing: LLM-optimized markdown extraction")

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
    from pathlib import Path

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
        click.echo("\n💡 LLM Usage Examples:")
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
            click.echo("\n🎯 Enhanced Mode Features:")
            click.echo(
                "   📑 Page chunks: Embedded as sections in single markdown files"
            )
            click.echo("   📊 Word positions: Embedded in hidden footer sections")
            click.echo("   📋 Table detection: Built-in with position data")
            click.echo("   🧠 Medical headers: Optimized for lab/imaging reports")
            click.echo("   🚫 Images: Disabled (text-only processing)")
    else:
        click.echo("❌ No files were converted")
        click.echo("💡 Check that the input directory exists and contains PDF files")
