"""
Utility functions for Wellbin medical data processing.

Contains common helper functions used across the package.
"""

import os
from pathlib import Path
from typing import Any, Callable, Optional, Tuple


def get_env_default(
    env_var: str, fallback: Any, convert_type: Optional[Callable[[str], Any]] = None
) -> Any:
    """Helper to get environment variable with proper empty value handling"""
    value = os.getenv(env_var, "").strip()
    if not value:
        value = fallback

    if convert_type == int:
        return int(value)
    elif convert_type == bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "yes", "on")
    return value


def get_env_or_default(
    env_var: str,
    default_value: Any,
    convert_type: Optional[Callable[[str], Any]] = None,
) -> Any:
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


def create_config_file() -> None:
    """Create a .env configuration file with default values and helpful comments"""
    import click

    env_file = Path(".env")

    # Check if .env already exists
    if env_file.exists():
        click.echo("⚠️  .env file already exists!")
        if not click.confirm("Do you want to overwrite it?"):
            click.echo("❌ Configuration file creation cancelled.")
            return

    # Configuration content with defaults and comments
    config_content = """# Wellbin Medical Data Scraper Configuration
# Generated with --config-init option
# Edit the values below to match your setup

# =============================================================================
# AUTHENTICATION - Required for Wellbin login
# =============================================================================
# Your Wellbin account email address
WELLBIN_EMAIL=your-email@example.com

# Your Wellbin account password
WELLBIN_PASSWORD=your-password

# =============================================================================
# SCRAPER CONFIGURATION - Optional overrides (defaults are in source code)
# =============================================================================

# Output directory for downloaded medical files
# Default: medical_data
WELLBIN_OUTPUT_DIR=medical_data

# Study download limit (0 = no limit, download all studies)
# Options: 0 (all), or any positive integer (1, 5, 10, etc.)
# Default: 0
WELLBIN_STUDY_LIMIT=0

# Study types to download
# Options: FhirStudy (lab reports), DicomStudy (imaging), all (both types)
# You can combine types with comma: FhirStudy,DicomStudy
# Default: FhirStudy
WELLBIN_STUDY_TYPES=FhirStudy

# Run browser in headless mode (no visible browser window)
# Options: true (headless), false (visible browser)
# Default: true
WELLBIN_HEADLESS=true

# =============================================================================
# CONVERTER CONFIGURATION - Optional overrides for PDF to Markdown conversion
# =============================================================================

# Input directory for PDF conversion (usually same as WELLBIN_OUTPUT_DIR)
# Default: medical_data
WELLBIN_INPUT_DIR=medical_data

# Output directory for markdown files
# Default: markdown_reports
WELLBIN_MARKDOWN_DIR=markdown_reports

# Preserve subdirectory structure from input
# Options: true (preserve structure), false (flat output)
# Default: true
WELLBIN_PRESERVE_STRUCTURE=true

# File type filter for conversion
# Options: lab (lab reports only), imaging (imaging only), all (both types)
# Default: all
WELLBIN_FILE_TYPE=all

# Enable enhanced mode with page chunks, tables, and word positions
# Options: true (enhanced features), false (standard mode)
# Default: false
WELLBIN_ENHANCED_MODE=false
"""

    try:
        # Write the configuration file
        with open(env_file, "w") as f:
            f.write(config_content)

        click.echo("✅ Configuration file created successfully!")
        click.echo(f"📁 Location: {env_file.absolute()}")
        click.echo()
        click.echo("🔧 Next steps:")
        click.echo("1. Edit .env file with your Wellbin credentials:")
        click.echo("   - Update WELLBIN_EMAIL with your email")
        click.echo("   - Update WELLBIN_PASSWORD with your password")
        click.echo()
        click.echo("2. Optionally customize other settings:")
        click.echo("   - WELLBIN_STUDY_TYPES: Choose what to download")
        click.echo("   - WELLBIN_STUDY_LIMIT: Limit number of studies")
        click.echo("   - WELLBIN_OUTPUT_DIR: Change output directory")
        click.echo("   - WELLBIN_ENHANCED_MODE: Enable advanced PDF conversion")
        click.echo()
        click.echo("3. Run the scraper:")
        click.echo("   uv run wellbin scrape")
        click.echo()
        click.echo("4. Convert PDFs to markdown:")
        click.echo("   uv run wellbin convert")
        click.echo()
        click.echo(
            "💡 All settings in .env can be overridden with command line options."
        )

    except Exception as e:
        click.echo(f"❌ Error creating configuration file: {e}")


def validate_credentials(email: str, password: str) -> Tuple[bool, str]:
    """Validate that credentials are provided and not default values"""
    if not email or email == "your-email@example.com":
        return False, "Email not configured. Please set WELLBIN_EMAIL or use --email"

    if not password or password == "your-password":
        return (
            False,
            "Password not configured. Please set WELLBIN_PASSWORD or use --password",
        )

    return True, "Credentials validated"
