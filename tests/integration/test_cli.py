"""
Tests for wellbin CLI commands.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from wellbin.cli import cli
from wellbin.commands.config import config


@pytest.mark.integration
class TestCLIMain:
    """Tests for main CLI entry point."""

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Wellbin Medical Data Downloader" in result.output
        assert "config" in result.output
        assert "scrape" in result.output
        assert "convert" in result.output

    def test_cli_version(self):
        """Test CLI version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        # Version should be displayed (exact format may vary)
        assert len(result.output.strip()) > 0


@pytest.mark.integration
class TestConfigCommand:
    """Tests for config command."""

    def test_config_command_help(self):
        """Test config command help."""
        runner = CliRunner()
        result = runner.invoke(config, ["--help"])

        assert result.exit_code == 0
        assert "Create a .env configuration file" in result.output

    def test_config_command_creates_file(self):
        """Test config command creates .env file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Mock the create_config_file function to avoid actual file creation
            with patch("wellbin.commands.config.create_config_file") as mock_create:
                result = runner.invoke(config)

                assert result.exit_code == 0
                mock_create.assert_called_once()

    def test_config_command_in_isolated_filesystem(self):
        """Test config command actually creates .env file in isolated filesystem."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Mock click.echo to suppress output during test
            with patch("click.echo"):
                result = runner.invoke(config)

                assert result.exit_code == 0

                # Check that .env file was created
                env_file = Path(".env")
                assert env_file.exists()

                content = env_file.read_text()
                assert "WELLBIN_EMAIL=your-email@example.com" in content
                assert "WELLBIN_PASSWORD=your-password" in content


@pytest.mark.integration
class TestScrapeCommand:
    """Tests for scrape command (without actual scraping)."""

    def test_scrape_command_help(self):
        """Test scrape command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["scrape", "--help"])

        assert result.exit_code == 0
        assert "Download medical data from Wellbin platform" in result.output
        assert "--email" in result.output
        assert "--password" in result.output
        assert "--dry-run" in result.output

    def test_scrape_command_missing_credentials(self):
        """Test scrape command fails with missing credentials."""
        runner = CliRunner()

        # Mock validate_credentials to return invalid
        with patch("wellbin.commands.scrape.validate_credentials") as mock_validate:
            mock_validate.return_value = (False, "Email not configured properly")

            result = runner.invoke(cli, ["scrape"])

            assert result.exit_code == 0  # Command runs but exits early with error message
            assert "❌" in result.output
            assert "uv run wellbin config" in result.output

    def test_scrape_command_dry_run_with_credentials(self):
        """Test scrape command dry run with valid credentials."""
        runner = CliRunner()

        # Mock the downloader to avoid actual web scraping
        with patch("wellbin.commands.scrape.WellbinMedicalDownloader") as mock_downloader:
            mock_instance = mock_downloader.return_value
            mock_instance.scrape_studies.return_value = []

            result = runner.invoke(
                cli,
                [
                    "scrape",
                    "--email",
                    "test@example.com",
                    "--password",
                    "testpass",
                    "--dry-run",
                ],
            )

            assert result.exit_code == 0
            assert "dry run" in result.output.lower()


@pytest.mark.integration
class TestConvertCommand:
    """Tests for convert command."""

    def test_convert_command_help(self):
        """Test convert command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["convert", "--help"])

        assert result.exit_code == 0
        assert "Convert medical PDFs to markdown" in result.output
        assert "--enhanced-mode" in result.output
        assert "--file-type" in result.output

    def test_convert_command_no_pdfs(self, tmp_path):
        """Test convert command with no PDF files."""
        runner = CliRunner()

        # Mock the converter to avoid actual PDF processing
        with (
            patch("wellbin.commands.convert.PDFToMarkdownConverter") as mock_converter,
            patch("wellbin.commands.convert.convert_structured_directories") as mock_structured,
        ):
            mock_instance = mock_converter.return_value
            mock_instance.convert_all_pdfs.return_value = []
            mock_structured.return_value = []

            result = runner.invoke(
                cli,
                [
                    "convert",
                    "--input-dir",
                    str(tmp_path),
                    "--output-dir",
                    str(tmp_path / "output"),
                ],
            )

            assert result.exit_code == 0
            # The command takes different paths based on preserve_structure flag and directory existence
            # Since we're not setting preserve_structure, it should use the converter directly
            if mock_converter.called:
                mock_converter.assert_called_once()
            elif mock_structured.called:
                mock_structured.assert_called_once()
            else:
                # Just verify the command ran successfully
                assert "Convert medical PDFs" in result.output or "No files were converted" in result.output

    def test_convert_command_enhanced_mode(self, tmp_path):
        """Test convert command with enhanced mode."""
        runner = CliRunner()

        with (
            patch("wellbin.commands.convert.PDFToMarkdownConverter") as mock_converter,
            patch("wellbin.commands.convert.convert_structured_directories") as mock_structured,
        ):
            mock_instance = mock_converter.return_value
            mock_instance.convert_all_pdfs.return_value = []
            mock_structured.return_value = []

            result = runner.invoke(
                cli,
                [
                    "convert",
                    "--enhanced-mode",
                    "--input-dir",
                    str(tmp_path),
                    "--output-dir",
                    str(tmp_path / "output"),
                ],
            )

            assert result.exit_code == 0
            # Just verify the command ran successfully with enhanced mode
            assert "Enhanced mode" in result.output
