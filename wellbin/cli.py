"""
Main CLI entry point for Wellbin medical data downloader.

Provides a unified command-line interface for downloading and processing
medical data from the Wellbin platform.
"""

import click
from dotenv import load_dotenv

from . import __version__
from .commands.config import config
from .commands.convert import convert
from .commands.scrape import scrape

# Load environment variables
load_dotenv()


@click.group()
@click.version_option(version=__version__, prog_name="wellbin")
@click.pass_context
def cli(ctx):
    """
    Wellbin Medical Data Downloader

    A comprehensive tool for downloading and processing medical data from the Wellbin platform.
    Supports both lab reports (FhirStudy) and medical imaging (DicomStudy) with PDF to Markdown conversion.

    WORKFLOW:
    1. Create configuration: wellbin config
    2. Download medical data: wellbin scrape
    3. Convert PDFs to markdown: wellbin convert

    CONFIGURATION:
    All commands support both environment variables (.env file) and command-line arguments.
    Command-line arguments take precedence over environment variables.

    Examples:
    \b
        # Setup and basic workflow
        uv run wellbin config              # Create .env configuration
        uv run wellbin scrape              # Download medical data
        uv run wellbin convert             # Convert PDFs to markdown

        # Advanced usage
        uv run wellbin scrape --types all --limit 10 --enhanced-mode
        uv run wellbin convert --enhanced-mode --file-type lab

        # Quick start (with inline credentials)
        uv run wellbin scrape --email user@example.com --password mypass --types FhirStudy
    """
    # Ensure context object exists
    ctx.ensure_object(dict)


# Add commands to the CLI group
cli.add_command(config)
cli.add_command(scrape)
cli.add_command(convert)


# Convenience function for programmatic access
def main():
    """Main entry point for the CLI application."""
    cli()


if __name__ == "__main__":
    main()
