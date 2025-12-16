"""
Scrape command for downloading medical data from Wellbin platform.
"""

from typing import Any, Optional

import click
from dotenv import load_dotenv

from ..core.scraper import WellbinMedicalDownloader
from ..core.utils import get_env_default, validate_credentials

# Load environment variables
load_dotenv()


@click.command()
@click.option("--email", "-e", help="Email for Wellbin login (overrides WELLBIN_EMAIL env var)")
@click.option(
    "--password",
    "-p",
    help="Password for Wellbin login (overrides WELLBIN_PASSWORD env var)",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    help="Limit number of studies to download, 0 = all (overrides WELLBIN_STUDY_LIMIT env var)",
)
@click.option(
    "--types",
    "-t",
    help='Study types to download: FhirStudy,DicomStudy or "all" (overrides WELLBIN_STUDY_TYPES env var)',
)
@click.option(
    "--output",
    "-o",
    help="Output directory for downloaded files (overrides WELLBIN_OUTPUT_DIR env var)",
)
@click.option(
    "--headless/--no-headless",
    default=None,
    help="Run browser in headless mode (overrides WELLBIN_HEADLESS env var)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be downloaded without actually downloading",
)
def scrape(
    email: Optional[str],
    password: Optional[str],
    limit: Optional[int],
    types: Optional[str],
    output: Optional[str],
    headless: Optional[bool],
    dry_run: bool,
) -> None:
    """
    Download medical data from Wellbin platform.

    Supports FhirStudy (lab reports) and DicomStudy (imaging reports) with proper categorization.

    ARGUMENT PRECEDENCE (highest to lowest):
    1. Command line arguments (--email, --limit, --types, etc.)
    2. Environment variables (WELLBIN_EMAIL, WELLBIN_STUDY_LIMIT, etc.)
    3. Built-in defaults

    Examples:
    \b
        # Download 5 lab reports
        uv run wellbin scrape --limit 5 --types FhirStudy

        # Download all imaging studies
        uv run wellbin scrape --limit 0 --types DicomStudy

        # Download both lab and imaging studies
        uv run wellbin scrape --types FhirStudy,DicomStudy

        # Download everything
        uv run wellbin scrape --types all

        # Dry run to see what would be downloaded
        uv run wellbin scrape --dry-run --types DicomStudy
    """

    # PROPER PRECEDENCE: CLI args override env vars override defaults
    final_email: str = email if email is not None else get_env_default("WELLBIN_EMAIL", "your-email@example.com")
    final_password: str = password if password is not None else get_env_default("WELLBIN_PASSWORD", "your-password")
    final_limit: int = limit if limit is not None else get_env_default("WELLBIN_STUDY_LIMIT", "0", int)
    final_types: str = types if types is not None else get_env_default("WELLBIN_STUDY_TYPES", "FhirStudy")
    final_output: str = output if output is not None else get_env_default("WELLBIN_OUTPUT_DIR", "medical_data")

    # For boolean flags: True/False if provided, otherwise check env var, otherwise default
    if headless is not None:
        final_headless: bool = headless
    else:
        final_headless = get_env_default("WELLBIN_HEADLESS", "true", bool)

    # Validate credentials
    is_valid, message = validate_credentials(final_email, final_password)
    if not is_valid:
        click.echo(f"❌ {message}")
        click.echo("💡 Use 'uv run wellbin config' to create a configuration file")
        return

    # Parse study types
    if final_types.lower() == "all":
        study_types = ["all"]
    else:
        study_types = [t.strip() for t in final_types.split(",")]

    # Convert limit
    final_limit_optional: Optional[int] = None if final_limit == 0 else final_limit

    # Display configuration
    click.echo("🚀 Wellbin Medical Data Downloader")
    click.echo("=" * 50)
    click.echo(f"📧 Email: {final_email}")
    click.echo(f"🔢 Study limit: {final_limit_optional if final_limit_optional else 'No limit (all studies)'}")
    click.echo(f"🎯 Study types: {', '.join(study_types)}")
    click.echo(f"📁 Output directory: {final_output}")
    click.echo(f"🤖 Headless mode: {final_headless}")
    if dry_run:
        click.echo("🔍 DRY RUN MODE: Will not download files")

    # Show precedence information
    click.echo("\n🔧 Argument Sources:")
    click.echo(f"   Email: {'CLI' if email else 'ENV/Default'}")
    click.echo(f"   Password: {'CLI' if password else 'ENV/Default'}")
    click.echo(f"   Limit: {'CLI' if limit is not None else 'ENV/Default'}")
    click.echo(f"   Types: {'CLI' if types else 'ENV/Default'}")
    click.echo(f"   Output: {'CLI' if output else 'ENV/Default'}")
    click.echo(f"   Headless: {'CLI' if headless is not None else 'ENV/Default'}")
    click.echo("=" * 50)

    if dry_run:
        click.echo("\n⚠️  This is a dry run. No files will be downloaded.")
        click.echo("Remove --dry-run flag to actually download files.")
        return

    # Create and run downloader
    downloader = WellbinMedicalDownloader(
        email=final_email,
        password=final_password,
        headless=final_headless,
        limit_studies=final_limit_optional,
        study_types=study_types,
        output_dir=final_output,
    )

    downloaded_files = downloader.scrape_studies()

    # Summary
    click.echo("\n" + "=" * 60)
    click.echo("🎉 DOWNLOAD COMPLETE!")
    click.echo("=" * 60)

    # Group by study type for summary
    by_type: dict[str, list[dict[str, Any]]] = {}

    if downloaded_files:
        click.echo(f"✅ Successfully downloaded {len(downloaded_files)} files:")

        for file_info in downloaded_files:
            study_type = file_info["study_type"]
            if study_type not in by_type:
                by_type[study_type] = []
            by_type[study_type].append(file_info)

        for study_type, files in by_type.items():
            config = downloader.study_config.get(study_type, {"icon": "📄", "description": study_type})
            click.echo(f"\n{config['icon']} {config['description']} ({len(files)} files):")
            for i, file_info in enumerate(files, 1):
                click.echo(f"  {i}. 📄 {file_info['local_path']}")
                click.echo(f"     📅 Study date: {file_info['study_date']}")
                click.echo(f"     📝 Description: {file_info['description']}")
    else:
        click.echo("❌ No files were downloaded")

    # Show organized directory structure
    if downloaded_files:
        click.echo(f"\n📁 Files organized in {final_output}/:")
        for study_type in by_type.keys():
            config = downloader.study_config.get(study_type, {"subdir": "unknown", "icon": "📄"})
            file_count = len(by_type[study_type])
            click.echo(f"  {config['icon']} {config['subdir']}/  ({file_count} files)")

        click.echo("\n💡 Next steps:")
        click.echo("   📄 Convert to markdown: uv run wellbin convert")
        click.echo(f"   🔍 View files: ls -la {final_output}/*/")
