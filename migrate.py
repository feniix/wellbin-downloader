#!/usr/bin/env python3
"""
Migration script for transitioning from old standalone scripts to new package structure.

This script helps users migrate from:
- wellbin_scrape_labs.py
- convert_pdfs_to_markdown.py

To the new unified CLI:
- uv run wellbin config
- uv run wellbin scrape
- uv run wellbin convert
"""

import shutil
from pathlib import Path
from typing import List

import click


@click.command()
@click.option(
    "--backup",
    is_flag=True,
    help="Create backup of old scripts before migration",
)
@click.option(
    "--clean",
    is_flag=True,
    help="Remove old scripts after successful migration",
)
def migrate(backup: bool, clean: bool) -> None:
    """
    Migrate from old standalone scripts to new package structure.

    This script will:
    1. Check for existing old scripts
    2. Optionally create backups
    3. Show migration commands
    4. Optionally clean up old files

    Args:
        backup: Whether to create backups of old scripts
        clean: Whether to remove old scripts after migration
    """

    click.echo("🔄 Wellbin Migration Tool")
    click.echo("=" * 50)

    # Check for old scripts
    old_scripts: List[str] = [
        "wellbin_scrape_labs.py",
        "convert_pdfs_to_markdown.py",
        "interactive_scraper.py",
    ]

    found_scripts: List[str] = []
    for script in old_scripts:
        if Path(script).exists():
            found_scripts.append(script)

    if not found_scripts:
        click.echo("✅ No old scripts found. You're already using the new structure!")
        click.echo("💡 Use 'uv run wellbin --help' to see available commands")
        return

    click.echo(f"📋 Found {len(found_scripts)} old scripts:")
    for script in found_scripts:
        click.echo(f"   - {script}")

    # Create backups if requested
    if backup:
        backup_dir: Path = Path("old_scripts_backup")
        backup_dir.mkdir(exist_ok=True)

        click.echo(f"\n📦 Creating backups in {backup_dir}/")
        for script in found_scripts:
            backup_path: Path = backup_dir / script
            shutil.copy2(script, backup_path)
            click.echo(f"   ✅ Backed up {script} -> {backup_path}")

    # Show migration guide
    click.echo("\n🚀 Migration Guide")
    click.echo("=" * 30)

    click.echo("\n1. OLD COMMAND EXAMPLES:")
    click.echo("   # Configuration")
    click.echo("   uv run python wellbin_scrape_labs.py --config-init")
    click.echo("   ")
    click.echo("   # Downloading")
    click.echo(
        "   uv run python wellbin_scrape_labs.py --email user@example.com --types all"
    )
    click.echo("   uv run python wellbin_scrape_labs.py --limit 10 --types FhirStudy")
    click.echo("   ")
    click.echo("   # Converting")
    click.echo("   uv run python convert_pdfs_to_markdown.py --enhanced-mode")
    click.echo("   uv run python convert_pdfs_to_markdown.py --file-type lab")

    click.echo("\n2. NEW COMMAND EQUIVALENTS:")
    click.echo("   # Configuration")
    click.echo("   uv run wellbin config")
    click.echo("   ")
    click.echo("   # Downloading")
    click.echo("   uv run wellbin scrape --email user@example.com --types all")
    click.echo("   uv run wellbin scrape --limit 10 --types FhirStudy")
    click.echo("   ")
    click.echo("   # Converting")
    click.echo("   uv run wellbin convert --enhanced-mode")
    click.echo("   uv run wellbin convert --file-type lab")

    click.echo("\n3. BENEFITS OF NEW STRUCTURE:")
    click.echo("   ✅ Single entry point: 'wellbin' command")
    click.echo("   ✅ Better help system: 'wellbin --help'")
    click.echo("   ✅ Subcommands: config, scrape, convert")
    click.echo("   ✅ Consistent argument handling")
    click.echo("   ✅ Proper Python package structure")
    click.echo("   ✅ Easier to extend and maintain")

    click.echo("\n4. QUICK START WITH NEW CLI:")
    click.echo("   uv run wellbin config              # Create .env file")
    click.echo("   uv run wellbin scrape              # Download medical data")
    click.echo("   uv run wellbin convert             # Convert to markdown")

    # Environment file migration
    env_path: Path = Path(".env")
    if env_path.exists():
        click.echo("\n📄 Environment File:")
        click.echo("   ✅ Found existing .env file")
        click.echo("   💡 Your configuration should work with the new CLI")
    else:
        click.echo("\n📄 Environment File:")
        click.echo("   ⚠️  No .env file found")
        click.echo("   💡 Run 'uv run wellbin config' to create one")

    # Clean up if requested
    if clean:
        click.echo("\n🧹 Cleaning up old scripts...")
        if not backup:
            if not click.confirm(
                "⚠️  You didn't create backups. Are you sure you want to delete the old scripts?"
            ):
                click.echo(
                    "❌ Cleanup cancelled. Use --backup flag to create backups first."
                )
                return

        for script in found_scripts:
            try:
                Path(script).unlink()
                click.echo(f"   🗑️  Removed {script}")
            except Exception as e:
                click.echo(f"   ❌ Failed to remove {script}: {e}")

    click.echo("\n🎉 Migration information complete!")
    click.echo("💡 Test the new CLI with: uv run wellbin --help")


if __name__ == "__main__":
    migrate()
