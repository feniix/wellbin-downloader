"""
Convert command for converting PDFs to markdown format.
"""

from dataclasses import dataclass
from pathlib import Path

import click
from dotenv import load_dotenv

from ..core.converter import PDFToMarkdownConverter, convert_structured_directories
from ..core.utils import get_env_or_default

# Load environment variables
load_dotenv()


@dataclass
class ConvertConfig:
    """Configuration for convert command."""

    input_dir: str = "medical_data"
    output_dir: str = "markdown_reports"
    preserve_structure: bool = True
    file_type: str = "all"
    enhanced_mode: bool = False

    # Source tracking for display
    input_source: str = "ENV/Default"
    output_source: str = "ENV/Default"
    file_type_source: str = "ENV/Default"
    preserve_source: str = "ENV/Default"
    enhanced_source: str = "ENV/Default"


def resolve_config(
    input_dir: str | None,
    output_dir: str | None,
    preserve_structure: bool,
    file_type: str | None,
    enhanced_mode: bool,
) -> ConvertConfig:
    """Resolve configuration from CLI args and environment variables.

    Args:
        input_dir: CLI input directory argument
        output_dir: CLI output directory argument
        preserve_structure: CLI preserve structure flag
        file_type: CLI file type argument
        enhanced_mode: CLI enhanced mode flag

    Returns:
        Resolved ConvertConfig
    """
    config = ConvertConfig()

    # Resolve input directory
    if input_dir is not None:
        config.input_dir = input_dir
        config.input_source = "CLI"
    else:
        config.input_dir = get_env_or_default("WELLBIN_INPUT_DIR", "medical_data")

    # Resolve output directory
    if output_dir is not None:
        config.output_dir = output_dir
        config.output_source = "CLI"
    else:
        config.output_dir = get_env_or_default("WELLBIN_MARKDOWN_DIR", "markdown_reports")

    # Resolve file type
    if file_type is not None:
        config.file_type = file_type
        config.file_type_source = "CLI"
    else:
        config.file_type = get_env_or_default("WELLBIN_FILE_TYPE", "all")

    # Resolve preserve structure
    if preserve_structure:
        config.preserve_structure = True
        config.preserve_source = "CLI"
    else:
        config.preserve_structure = get_env_or_default("WELLBIN_PRESERVE_STRUCTURE", "true", bool)

    # Resolve enhanced mode
    if enhanced_mode:
        config.enhanced_mode = True
        config.enhanced_source = "CLI"
    else:
        config.enhanced_mode = get_env_or_default("WELLBIN_ENHANCED_MODE", "false", bool)

    return config


def display_config(config: ConvertConfig) -> None:
    """Display configuration summary.

    Args:
        config: Convert configuration
    """
    click.echo("🔄 PDF to Markdown Converter for Medical Reports")
    click.echo("🤖 Optimized for LLM consumption using PyMuPDF4LLM")
    click.echo("=" * 60)

    click.echo(f"📂 Input directory: {config.input_dir}")
    click.echo(f"📁 Output directory: {config.output_dir}")
    click.echo(f"🎯 File type filter: {config.file_type}")
    click.echo("🧠 Processing: LLM-optimized markdown extraction")

    if config.preserve_structure:
        click.echo("📁 Preserving subdirectory structure")
    if config.enhanced_mode:
        click.echo("🎯 Enhanced mode: embedded page chunks + tables + word positions (no images)")

    click.echo("\n🔧 Argument Sources:")
    click.echo(f"   Input dir: {config.input_source}")
    click.echo(f"   Output dir: {config.output_source}")
    click.echo(f"   File type: {config.file_type_source}")
    click.echo(f"   Preserve structure: {config.preserve_source}")
    click.echo(f"   Enhanced mode: {config.enhanced_source}")
    click.echo()


def run_conversion(config: ConvertConfig) -> list[Path]:
    """Run the conversion based on configuration.

    Args:
        config: Convert configuration

    Returns:
        List of converted file paths
    """
    if config.preserve_structure and Path(config.input_dir).exists():
        return convert_structured_directories(
            config.input_dir,
            config.output_dir,
            config.file_type,
            config.enhanced_mode,
        )

    # Create converter and run conversion on flat directory
    converter = PDFToMarkdownConverter(
        config.input_dir,
        config.output_dir,
        config.enhanced_mode,
    )
    return converter.convert_all_pdfs()


def display_success_info(output_dir: str, enhanced_mode: bool) -> None:
    """Display success information and LLM usage examples.

    Args:
        output_dir: Output directory path
        enhanced_mode: Whether enhanced mode was used
    """
    click.echo("\n💡 LLM Usage Examples:")
    click.echo(f"   📖 Read a report: cat {output_dir}/20250604-lab-0.md")
    click.echo(f"   🔍 Search all reports: grep -r 'keyword' {output_dir}/")
    click.echo(f"   📊 Count total reports: find {output_dir} -name '*.md' | wc -l")
    click.echo(f"   🤖 Feed to LLM: cat {output_dir}/**/*.md | llm 'analyze trends'")
    click.echo(f"   📈 Extract lab values: grep -h 'mg/dL\\|g/dL' {output_dir}/**/*.md")
    click.echo(f"   🔬 Find abnormal: grep -i 'alto\\|bajo\\|high\\|low' {output_dir}/**/*.md")

    if enhanced_mode:
        click.echo("\n🎯 Enhanced Mode Features:")
        click.echo("   📑 Page chunks: Embedded as sections in single markdown files")
        click.echo("   📊 Word positions: Embedded in hidden footer sections")
        click.echo("   📋 Table detection: Built-in with position data")
        click.echo("   🧠 Medical headers: Optimized for lab/imaging reports")
        click.echo("   🚫 Images: Disabled (text-only processing)")


def display_failure_info() -> None:
    """Display failure information."""
    click.echo("❌ No files were converted")
    click.echo("💡 Check that the input directory exists and contains PDF files")


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
def convert(
    input_dir: str | None,
    output_dir: str | None,
    preserve_structure: bool,
    file_type: str | None,
    enhanced_mode: bool,
) -> None:
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
    config = resolve_config(input_dir, output_dir, preserve_structure, file_type, enhanced_mode)
    display_config(config)

    converted_files = run_conversion(config)

    if converted_files:
        display_success_info(config.output_dir, config.enhanced_mode)
    else:
        display_failure_info()
