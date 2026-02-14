"""
Scrape command for downloading medical data from Wellbin platform.
"""

from dataclasses import dataclass, field

import click
from dotenv import load_dotenv

from ..core.scraper import DownloadResult, WellbinMedicalDownloader
from ..core.utils import get_env_or_default, validate_credentials

# Load environment variables
load_dotenv()


@dataclass
class ScrapeConfig:
    """Configuration for scrape command."""

    email: str = ""
    password: str = ""
    limit: int | None = None
    study_types: list[str] = field(default_factory=lambda: ["FhirStudy"])
    output_dir: str = "medical_data"
    headless: bool = True

    # Source tracking for display
    email_source: str = "ENV/Default"
    password_source: str = "ENV/Default"
    limit_source: str = "ENV/Default"
    types_source: str = "ENV/Default"
    output_source: str = "ENV/Default"
    headless_source: str = "ENV/Default"


def resolve_config(
    email: str | None,
    password: str | None,
    limit: int | None,
    types: str | None,
    output: str | None,
    headless: bool | None,
) -> ScrapeConfig:
    """Resolve configuration from CLI args and environment variables.

    Args:
        email: CLI email argument
        password: CLI password argument
        limit: CLI limit argument
        types: CLI types argument
        output: CLI output argument
        headless: CLI headless argument

    Returns:
        Resolved ScrapeConfig
    """
    config = ScrapeConfig()

    # Resolve email
    if email is not None:
        config.email = email
        config.email_source = "CLI"
    else:
        config.email = get_env_or_default("WELLBIN_EMAIL", "your-email@example.com")

    # Resolve password
    if password is not None:
        config.password = password
        config.password_source = "CLI"
    else:
        config.password = get_env_or_default("WELLBIN_PASSWORD", "your-password")

    # Resolve limit
    if limit is not None:
        config.limit = None if limit == 0 else limit
        config.limit_source = "CLI"
    else:
        limit_val = get_env_or_default("WELLBIN_STUDY_LIMIT", "0", int)
        config.limit = None if limit_val == 0 else limit_val

    # Resolve types
    if types is not None:
        config.study_types = _parse_study_types(types)
        config.types_source = "CLI"
    else:
        types_str = get_env_or_default("WELLBIN_STUDY_TYPES", "FhirStudy")
        config.study_types = _parse_study_types(types_str)

    # Resolve output
    if output is not None:
        config.output_dir = output
        config.output_source = "CLI"
    else:
        config.output_dir = get_env_or_default("WELLBIN_OUTPUT_DIR", "medical_data")

    # Resolve headless
    if headless is not None:
        config.headless = headless
        config.headless_source = "CLI"
    else:
        config.headless = get_env_or_default("WELLBIN_HEADLESS", "true", bool)

    return config


def _parse_study_types(types_str: str) -> list[str]:
    """Parse study types string into list.

    Args:
        types_str: Comma-separated study types or "all"

    Returns:
        List of study types
    """
    if types_str.lower() == "all":
        return ["all"]
    return [t.strip() for t in types_str.split(",")]


def display_config(config: ScrapeConfig, dry_run: bool) -> None:
    """Display configuration summary.

    Args:
        config: Scraped configuration
        dry_run: Whether this is a dry run
    """
    click.echo("🚀 Wellbin Medical Data Downloader")
    click.echo("=" * 50)
    click.echo(f"📧 Email: {config.email}")
    click.echo(f"🔢 Study limit: {config.limit if config.limit else 'No limit (all studies)'}")
    click.echo(f"🎯 Study types: {', '.join(config.study_types)}")
    click.echo(f"📁 Output directory: {config.output_dir}")
    click.echo(f"🤖 Headless mode: {config.headless}")

    if dry_run:
        click.echo("🔍 DRY RUN MODE: Will not download files")

    click.echo("\n🔧 Argument Sources:")
    click.echo(f"   Email: {config.email_source}")
    click.echo(f"   Password: {config.password_source}")
    click.echo(f"   Limit: {config.limit_source}")
    click.echo(f"   Types: {config.types_source}")
    click.echo(f"   Output: {config.output_source}")
    click.echo(f"   Headless: {config.headless_source}")
    click.echo("=" * 50)


def display_summary(
    downloaded_files: list[DownloadResult],
    downloader: WellbinMedicalDownloader,
    output_dir: str,
) -> None:
    """Display download summary.

    Args:
        downloaded_files: List of download results
        downloader: Downloader instance with study config
        output_dir: Output directory path
    """
    click.echo("\n" + "=" * 60)
    click.echo("🎉 DOWNLOAD COMPLETE!")
    click.echo("=" * 60)

    if not downloaded_files:
        click.echo("❌ No files were downloaded")
        return

    by_type = _group_files_by_type(downloaded_files)

    click.echo(f"✅ Successfully downloaded {len(downloaded_files)} files:")

    for study_type, files in by_type.items():
        _display_type_summary(study_type, files, downloader)

    _display_directory_structure(by_type, downloader, output_dir)
    _display_next_steps(output_dir)


def _group_files_by_type(files: list[DownloadResult]) -> dict[str, list[DownloadResult]]:
    """Group downloaded files by study type."""
    by_type: dict[str, list[DownloadResult]] = {}
    for file_info in files:
        study_type = file_info.study_type
        if study_type not in by_type:
            by_type[study_type] = []
        by_type[study_type].append(file_info)
    return by_type


def _display_type_summary(
    study_type: str,
    files: list[DownloadResult],
    downloader: WellbinMedicalDownloader,
) -> None:
    """Display summary for a single study type."""
    config = downloader.study_config.get(study_type, {"icon": "📄", "description": study_type})
    click.echo(f"\n{config['icon']} {config['description']} ({len(files)} files):")

    for i, file_info in enumerate(files, 1):
        click.echo(f"  {i}. 📄 {file_info.local_path}")
        click.echo(f"     📅 Study date: {file_info.study_date}")
        click.echo(f"     📝 Description: {file_info.description}")


def _display_directory_structure(
    by_type: dict[str, list[DownloadResult]],
    downloader: WellbinMedicalDownloader,
    output_dir: str,
) -> None:
    """Display organized directory structure."""
    click.echo(f"\n📁 Files organized in {output_dir}/:")

    for study_type in by_type.keys():
        config = downloader.study_config.get(study_type, {"subdir": "unknown", "icon": "📄"})
        file_count = len(by_type[study_type])
        click.echo(f"  {config['icon']} {config['subdir']}/  ({file_count} files)")


def _display_next_steps(output_dir: str) -> None:
    """Display next steps for the user."""
    click.echo("\n💡 Next steps:")
    click.echo("   📄 Convert to markdown: uv run wellbin convert")
    click.echo(f"   🔍 View files: ls -la {output_dir}/*/")


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
    email: str | None,
    password: str | None,
    limit: int | None,
    types: str | None,
    output: str | None,
    headless: bool | None,
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
    config = resolve_config(email, password, limit, types, output, headless)

    # Validate credentials
    is_valid, message = validate_credentials(config.email, config.password)
    if not is_valid:
        click.echo(f"❌ {message}")
        click.echo("💡 Use 'uv run wellbin config' to create a configuration file")
        return

    display_config(config, dry_run)

    if dry_run:
        click.echo("\n⚠️  This is a dry run. No files will be downloaded.")
        click.echo("Remove --dry-run flag to actually download files.")
        return

    # Create and run downloader
    downloader = WellbinMedicalDownloader(
        email=config.email,
        password=config.password,
        headless=config.headless,
        limit_studies=config.limit,
        study_types=config.study_types,
        output_dir=config.output_dir,
    )

    downloaded_files = downloader.scrape_studies()
    display_summary(downloaded_files, downloader, config.output_dir)
