"""Unit tests for wellbin/commands/convert.py.

Focus on config resolution and helper functions.
"""

from unittest.mock import patch

import pytest

from wellbin.commands.convert import (
    ConvertConfig,
    resolve_config,
)


@pytest.mark.unit
class TestConvertConfig:
    """Tests for ConvertConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ConvertConfig()

        assert config.input_dir == "medical_data"
        assert config.output_dir == "markdown_reports"
        assert config.preserve_structure is True
        assert config.file_type == "all"
        assert config.enhanced_mode is False

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ConvertConfig(
            input_dir="/custom/input",
            output_dir="/custom/output",
            preserve_structure=False,
            file_type="lab",
            enhanced_mode=True,
        )

        assert config.input_dir == "/custom/input"
        assert config.output_dir == "/custom/output"
        assert config.preserve_structure is False
        assert config.file_type == "lab"
        assert config.enhanced_mode is True


@pytest.mark.unit
class TestResolveConvertConfig:
    """Tests for resolve_config function in convert module."""

    @patch("wellbin.commands.convert.get_env_or_default")
    def test_all_cli_args_override_env(self, mock_get_env) -> None:
        """Test that CLI args override environment variables."""
        mock_get_env.return_value = "env_value"

        config = resolve_config(
            input_dir="/cli/input",
            output_dir="/cli/output",
            preserve_structure=True,  # CLI flag
            file_type="imaging",
            enhanced_mode=True,  # CLI flag
        )

        assert config.input_dir == "/cli/input"
        assert config.input_source == "CLI"
        assert config.output_dir == "/cli/output"
        assert config.output_source == "CLI"
        assert config.preserve_structure is True
        assert config.preserve_source == "CLI"
        assert config.file_type == "imaging"
        assert config.file_type_source == "CLI"
        assert config.enhanced_mode is True
        assert config.enhanced_source == "CLI"

    @patch("wellbin.commands.convert.get_env_or_default")
    def test_uses_env_when_cli_not_provided(self, mock_get_env) -> None:
        """Test that environment variables are used when CLI args not provided."""

        def mock_side_effect(key, default, *args):
            if key == "WELLBIN_INPUT_DIR":
                return "/env/input"
            if key == "WELLBIN_MARKDOWN_DIR":
                return "/env/output"
            if key == "WELLBIN_FILE_TYPE":
                return "lab"
            if key == "WELLBIN_PRESERVE_STRUCTURE":
                return False  # Type-converted to bool
            if key == "WELLBIN_ENHANCED_MODE":
                return True  # Type-converted to bool
            return default

        mock_get_env.side_effect = mock_side_effect

        config = resolve_config(
            input_dir=None,
            output_dir=None,
            preserve_structure=False,  # Use env
            file_type=None,
            enhanced_mode=False,  # Use env
        )

        assert config.input_dir == "/env/input"
        assert config.output_dir == "/env/output"
        assert config.file_type == "lab"
        # These should come from env since CLI flags are False
        assert config.preserve_structure is False
        assert config.enhanced_mode is True

    @patch("wellbin.commands.convert.get_env_or_default")
    def test_preserve_structure_cli_true(self, mock_get_env) -> None:
        """Test preserve_structure=True from CLI."""
        mock_get_env.return_value = "false"

        config = resolve_config(
            input_dir=None,
            output_dir=None,
            preserve_structure=True,
            file_type=None,
            enhanced_mode=False,
        )

        assert config.preserve_structure is True
        assert config.preserve_source == "CLI"

    @patch("wellbin.commands.convert.get_env_or_default")
    def test_enhanced_mode_cli_true(self, mock_get_env) -> None:
        """Test enhanced_mode=True from CLI."""
        mock_get_env.return_value = "false"

        config = resolve_config(
            input_dir=None,
            output_dir=None,
            preserve_structure=False,
            file_type=None,
            enhanced_mode=True,
        )

        assert config.enhanced_mode is True
        assert config.enhanced_source == "CLI"

    @patch("wellbin.commands.convert.get_env_or_default")
    def test_file_type_lab(self, mock_get_env) -> None:
        """Test file_type=lab from CLI."""
        mock_get_env.return_value = "all"

        config = resolve_config(
            input_dir=None,
            output_dir=None,
            preserve_structure=False,
            file_type="lab",
            enhanced_mode=False,
        )

        assert config.file_type == "lab"
        assert config.file_type_source == "CLI"

    @patch("wellbin.commands.convert.get_env_or_default")
    def test_file_type_imaging(self, mock_get_env) -> None:
        """Test file_type=imaging from CLI."""
        mock_get_env.return_value = "all"

        config = resolve_config(
            input_dir=None,
            output_dir=None,
            preserve_structure=False,
            file_type="imaging",
            enhanced_mode=False,
        )

        assert config.file_type == "imaging"
        assert config.file_type_source == "CLI"

    @patch("wellbin.commands.convert.get_env_or_default")
    def test_partial_cli_overrides(self, mock_get_env) -> None:
        """Test that partial CLI args only override those specific values."""

        def mock_side_effect(key, default, *args):
            if key == "WELLBIN_INPUT_DIR":
                return "/env/input"
            if key == "WELLBIN_MARKDOWN_DIR":
                return "/env/output"
            if key == "WELLBIN_FILE_TYPE":
                return "all"
            if key == "WELLBIN_PRESERVE_STRUCTURE":
                return True  # Type-converted to bool
            if key == "WELLBIN_ENHANCED_MODE":
                return False  # Type-converted to bool
            return default

        mock_get_env.side_effect = mock_side_effect

        # Only override input_dir and enhanced_mode
        config = resolve_config(
            input_dir="/cli/input",
            output_dir=None,  # Use env
            preserve_structure=False,  # Use env
            file_type=None,  # Use env
            enhanced_mode=True,  # Override env
        )

        assert config.input_dir == "/cli/input"
        assert config.input_source == "CLI"
        assert config.output_dir == "/env/output"
        assert config.output_source == "ENV/Default"
        assert config.file_type == "all"
        assert config.file_type_source == "ENV/Default"
        assert config.preserve_structure is True  # From env
        assert config.enhanced_mode is True  # From CLI
        assert config.enhanced_source == "CLI"
