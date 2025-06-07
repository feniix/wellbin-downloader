"""
Config command for creating and managing configuration files.
"""

import click

from ..core.utils import create_config_file


@click.command()
def config() -> None:
    """
    Create a .env configuration file with default values and helpful comments.

    This command creates a comprehensive configuration file that includes:
    - Authentication settings (email, password)
    - Scraper configuration (study types, limits, output directories)
    - Converter configuration (enhanced mode, file types, structure preservation)

    The generated .env file contains detailed comments explaining each option
    and can be customized to match your specific needs.

    Examples:
    \b
        # Create configuration file
        uv run wellbin config

        # After editing .env, run scraper
        uv run wellbin scrape

        # Convert downloaded PDFs
        uv run wellbin convert
    """
    create_config_file()
