"""
Tests for wellbin.core.utils module.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from wellbin.core.utils import (
    create_config_file,
    get_env_default,
    get_env_or_default,
    validate_credentials,
)


class TestGetEnvDefault:
    """Tests for get_env_default function."""

    def test_get_env_default_with_existing_value(self):
        """Test getting existing environment variable."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = get_env_default("TEST_VAR", "default_value")
            assert result == "test_value"

    def test_get_env_default_with_missing_value(self):
        """Test fallback to default when env var is missing."""
        result = get_env_default("NONEXISTENT_VAR", "default_value")
        assert result == "default_value"

    def test_get_env_default_with_empty_value(self):
        """Test fallback to default when env var is empty."""
        with patch.dict(os.environ, {"EMPTY_VAR": ""}):
            result = get_env_default("EMPTY_VAR", "default_value")
            assert result == "default_value"

    def test_get_env_default_with_whitespace_value(self):
        """Test fallback to default when env var contains only whitespace."""
        with patch.dict(os.environ, {"WHITESPACE_VAR": "   "}):
            result = get_env_default("WHITESPACE_VAR", "default_value")
            assert result == "default_value"

    def test_get_env_default_int_conversion(self):
        """Test integer type conversion."""
        with patch.dict(os.environ, {"INT_VAR": "42"}):
            result = get_env_default("INT_VAR", "0", int)
            assert result == 42

    def test_get_env_default_bool_conversion_true(self):
        """Test boolean type conversion for true values."""
        test_cases = ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]
        for value in test_cases:
            with patch.dict(os.environ, {"BOOL_VAR": value}):
                result = get_env_default("BOOL_VAR", False, bool)
                assert result is True, f"Failed for value: {value}"

    def test_get_env_default_bool_conversion_false(self):
        """Test boolean type conversion for false values."""
        test_cases = ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF"]
        for value in test_cases:
            with patch.dict(os.environ, {"BOOL_VAR": value}):
                result = get_env_default("BOOL_VAR", True, bool)
                assert result is False, f"Failed for value: {value}"


class TestGetEnvOrDefault:
    """Tests for get_env_or_default function."""

    def test_get_env_or_default_with_existing_value(self):
        """Test getting existing environment variable."""
        with patch.dict(os.environ, {"TEST_VAR": "env_value"}):
            result = get_env_or_default("TEST_VAR", "default_value")
            assert result == "env_value"

    def test_get_env_or_default_with_default(self):
        """Test fallback to default value."""
        result = get_env_or_default("NONEXISTENT_VAR", "default_value")
        assert result == "default_value"

    def test_get_env_or_default_int_conversion(self):
        """Test integer conversion with fallback."""
        with patch.dict(os.environ, {"INT_VAR": "100"}):
            result = get_env_or_default("INT_VAR", 50, int)
            assert result == 100

    def test_get_env_or_default_int_fallback(self):
        """Test integer fallback when env var is missing."""
        result = get_env_or_default("MISSING_INT_VAR", 50, int)
        assert result == 50


class TestValidateCredentials:
    """Tests for validate_credentials function."""

    def test_validate_credentials_valid(self):
        """Test validation with valid credentials."""
        is_valid, message = validate_credentials("user@example.com", "mypassword")
        assert is_valid is True
        assert message == "Credentials validated"

    def test_validate_credentials_empty_email(self):
        """Test validation with empty email."""
        is_valid, message = validate_credentials("", "mypassword")
        assert is_valid is False
        assert "Email not configured" in message

    def test_validate_credentials_default_email(self):
        """Test validation with default email placeholder."""
        is_valid, message = validate_credentials("your-email@example.com", "mypassword")
        assert is_valid is False
        assert "Email not configured" in message

    def test_validate_credentials_empty_password(self):
        """Test validation with empty password."""
        is_valid, message = validate_credentials("user@example.com", "")
        assert is_valid is False
        assert "Password not configured" in message

    def test_validate_credentials_default_password(self):
        """Test validation with default password placeholder."""
        is_valid, message = validate_credentials("user@example.com", "your-password")
        assert is_valid is False
        assert "Password not configured" in message


class TestCreateConfigFile:
    """Tests for create_config_file function."""

    def test_create_config_file_new(self, temp_dir, monkeypatch):
        """Test creating new config file."""
        # Change to temp directory
        monkeypatch.chdir(temp_dir)

        # Mock click module functions
        with patch("click.echo"):
            create_config_file()

        env_file = temp_dir / ".env"
        assert env_file.exists()

        content = env_file.read_text()
        assert "WELLBIN_EMAIL=your-email@example.com" in content
        assert "WELLBIN_PASSWORD=your-password" in content
        assert "WELLBIN_OUTPUT_DIR=medical_data" in content

    def test_create_config_file_existing_no_overwrite(self, temp_dir, monkeypatch):
        """Test handling existing config file without overwrite."""
        # Change to temp directory
        monkeypatch.chdir(temp_dir)

        # Create existing .env file
        env_file = temp_dir / ".env"
        env_file.write_text("EXISTING_CONFIG=true")
        original_content = env_file.read_text()

        # Mock click functions
        with patch("click.echo"), patch("click.confirm", return_value=False):
            create_config_file()

        # File should remain unchanged
        assert env_file.read_text() == original_content

    def test_create_config_file_existing_with_overwrite(self, temp_dir, monkeypatch):
        """Test overwriting existing config file."""
        # Change to temp directory
        monkeypatch.chdir(temp_dir)

        # Create existing .env file
        env_file = temp_dir / ".env"
        env_file.write_text("EXISTING_CONFIG=true")

        # Mock click functions to confirm overwrite
        with patch("click.echo"), patch("click.confirm", return_value=True):
            create_config_file()

        # File should be overwritten with new content
        content = env_file.read_text()
        assert "WELLBIN_EMAIL=your-email@example.com" in content
        assert "EXISTING_CONFIG=true" not in content
