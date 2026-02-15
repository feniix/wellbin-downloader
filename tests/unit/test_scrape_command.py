"""Unit tests for wellbin/commands/scrape.py.

Focus on config resolution and helper functions.
"""

from unittest.mock import patch

from wellbin.commands.scrape import (
    ScrapeConfig,
    _parse_study_types,
    resolve_config,
)


class TestScrapeConfig:
    """Tests for ScrapeConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ScrapeConfig()

        assert config.email == ""
        assert config.password == ""
        assert config.limit is None
        assert config.study_types == ["FhirStudy"]
        assert config.output_dir == "medical_data"
        assert config.headless is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ScrapeConfig(
            email="test@example.com",
            password="secret",
            limit=10,
            study_types=["DicomStudy"],
            output_dir="/custom/path",
            headless=False,
        )

        assert config.email == "test@example.com"
        assert config.password == "secret"
        assert config.limit == 10
        assert config.study_types == ["DicomStudy"]
        assert config.output_dir == "/custom/path"
        assert config.headless is False


class TestParseStudyTypes:
    """Tests for _parse_study_types function."""

    def test_single_type(self) -> None:
        """Test parsing single study type."""
        result = _parse_study_types("FhirStudy")
        assert result == ["FhirStudy"]

    def test_multiple_types(self) -> None:
        """Test parsing multiple study types."""
        result = _parse_study_types("FhirStudy,DicomStudy")
        assert result == ["FhirStudy", "DicomStudy"]

    def test_multiple_types_with_spaces(self) -> None:
        """Test parsing study types with spaces."""
        result = _parse_study_types("FhirStudy, DicomStudy, OtherType")
        assert result == ["FhirStudy", "DicomStudy", "OtherType"]

    def test_all_keyword_lowercase(self) -> None:
        """Test 'all' keyword (lowercase)."""
        result = _parse_study_types("all")
        assert result == ["all"]

    def test_all_keyword_uppercase(self) -> None:
        """Test 'ALL' keyword (uppercase)."""
        result = _parse_study_types("ALL")
        assert result == ["all"]

    def test_all_keyword_mixed_case(self) -> None:
        """Test 'All' keyword (mixed case)."""
        result = _parse_study_types("All")
        assert result == ["all"]


class TestResolveConfig:
    """Tests for resolve_config function."""

    @patch("wellbin.commands.scrape.get_env_or_default")
    def test_all_cli_args_override_env(self, mock_get_env: "patch") -> None:
        """Test that CLI args override environment variables."""
        mock_get_env.return_value = "env_value"

        config = resolve_config(
            email="cli@example.com",
            password="clipass",
            limit=5,
            types="DicomStudy",
            output="/cli/output",
            headless=False,
        )

        assert config.email == "cli@example.com"
        assert config.email_source == "CLI"
        assert config.password == "clipass"
        assert config.password_source == "CLI"
        assert config.limit == 5
        assert config.limit_source == "CLI"
        assert config.study_types == ["DicomStudy"]
        assert config.types_source == "CLI"
        assert config.output_dir == "/cli/output"
        assert config.output_source == "CLI"
        assert config.headless is False
        assert config.headless_source == "CLI"

    @patch("wellbin.commands.scrape.get_env_or_default")
    def test_uses_env_when_cli_not_provided(self, mock_get_env) -> None:
        """Test that environment variables are used when CLI args not provided."""

        def mock_side_effect(key, default, *args):
            # Simulate get_env_or_default behavior with type conversion
            if key == "WELLBIN_EMAIL":
                return "env@example.com"
            if key == "WELLBIN_PASSWORD":
                return "envpass"
            if key == "WELLBIN_STUDY_LIMIT":
                return 10  # Type-converted to int
            if key == "WELLBIN_STUDY_TYPES":
                return "DicomStudy"
            if key == "WELLBIN_OUTPUT_DIR":
                return "/env/output"
            if key == "WELLBIN_HEADLESS":
                return False  # Type-converted to bool
            return default

        mock_get_env.side_effect = mock_side_effect

        config = resolve_config(
            email=None,
            password=None,
            limit=None,
            types=None,
            output=None,
            headless=None,
        )

        assert config.email == "env@example.com"
        assert config.password == "envpass"
        assert config.limit == 10
        assert config.study_types == ["DicomStudy"]
        assert config.output_dir == "/env/output"
        assert config.headless is False

    @patch("wellbin.commands.scrape.get_env_or_default")
    def test_limit_zero_becomes_none(self, mock_get_env: "patch") -> None:
        """Test that limit=0 is converted to None (no limit)."""
        mock_get_env.return_value = "default"

        config = resolve_config(
            email=None,
            password=None,
            limit=0,
            types=None,
            output=None,
            headless=None,
        )

        assert config.limit is None
        assert config.limit_source == "CLI"

    @patch("wellbin.commands.scrape.get_env_or_default")
    def test_env_limit_zero_becomes_none(self, mock_get_env) -> None:
        """Test that env limit=0 is converted to None (no limit)."""

        def mock_side_effect(key, default, *args):
            if key == "WELLBIN_STUDY_LIMIT":
                return 0  # Type-converted to int
            return default

        mock_get_env.side_effect = mock_side_effect

        config = resolve_config(
            email=None,
            password=None,
            limit=None,
            types=None,
            output=None,
            headless=None,
        )

        assert config.limit is None

    @patch("wellbin.commands.scrape.get_env_or_default")
    def test_types_all_from_cli(self, mock_get_env: "patch") -> None:
        """Test 'all' types from CLI."""
        mock_get_env.return_value = "default"

        config = resolve_config(
            email=None,
            password=None,
            limit=None,
            types="all",
            output=None,
            headless=None,
        )

        assert config.study_types == ["all"]
        assert config.types_source == "CLI"

    @patch("wellbin.commands.scrape.get_env_or_default")
    def test_partial_cli_overrides(self, mock_get_env) -> None:
        """Test that partial CLI args only override those specific values."""

        def mock_side_effect(key, default, *args):
            if key == "WELLBIN_EMAIL":
                return "env@example.com"
            if key == "WELLBIN_PASSWORD":
                return "envpass"
            if key == "WELLBIN_STUDY_LIMIT":
                return 20  # Type-converted to int
            if key == "WELLBIN_STUDY_TYPES":
                return "FhirStudy"
            if key == "WELLBIN_OUTPUT_DIR":
                return "env_output"
            if key == "WELLBIN_HEADLESS":
                return True  # Type-converted to bool
            return default

        mock_get_env.side_effect = mock_side_effect

        # Only override email and limit
        config = resolve_config(
            email="cli@example.com",
            password=None,  # Use env
            limit=5,  # Override env
            types=None,  # Use env
            output=None,  # Use env
            headless=None,  # Use env
        )

        assert config.email == "cli@example.com"
        assert config.email_source == "CLI"
        assert config.password == "envpass"
        assert config.password_source == "ENV/Default"
        assert config.limit == 5
        assert config.limit_source == "CLI"
        assert config.study_types == ["FhirStudy"]
        assert config.output_dir == "env_output"
        assert config.headless is True

    @patch("wellbin.commands.scrape.get_env_or_default")
    def test_headless_true_from_env(self, mock_get_env) -> None:
        """Test headless=true from environment."""

        def mock_side_effect(key, default, *args):
            if key == "WELLBIN_HEADLESS":
                return True  # Type-converted to bool
            return default

        mock_get_env.side_effect = mock_side_effect

        config = resolve_config(
            email=None,
            password=None,
            limit=None,
            types=None,
            output=None,
            headless=None,
        )

        assert config.headless is True

    @patch("wellbin.commands.scrape.get_env_or_default")
    def test_headless_false_from_env(self, mock_get_env) -> None:
        """Test headless=false from environment."""

        def mock_side_effect(key, default, *args):
            if key == "WELLBIN_HEADLESS":
                return False  # Type-converted to bool
            return default

        mock_get_env.side_effect = mock_side_effect

        config = resolve_config(
            email=None,
            password=None,
            limit=None,
            types=None,
            output=None,
            headless=None,
        )

        assert config.headless is False
