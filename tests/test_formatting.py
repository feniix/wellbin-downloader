"""
Tests for wellbin.core.formatting module.
"""

from io import StringIO
from unittest.mock import patch

from wellbin.core.formatting import (
    DOMAIN_EMOJIS,
    EMOJI_PREFIXES,
    OutputLevel,
    complete,
    converting,
    date_info,
    debug,
    downloading,
    emit,
    emit_file_saved,
    emit_header,
    emit_key_value,
    emit_list,
    emit_separator,
    emit_with_emoji,
    error,
    file_info,
    folder_info,
    format_bytes,
    info,
    processing,
    size_info,
    success,
    url_info,
    warning,
)


class TestOutputLevel:
    """Tests for OutputLevel enum."""

    def test_output_level_values(self):
        """Test that OutputLevel has expected values."""
        assert OutputLevel.INFO.value == "info"
        assert OutputLevel.SUCCESS.value == "success"
        assert OutputLevel.WARNING.value == "warning"
        assert OutputLevel.ERROR.value == "error"
        assert OutputLevel.DEBUG.value == "debug"


class TestEmojiPrefixes:
    """Tests for emoji prefix constants."""

    def test_emoji_prefixes_exist(self):
        """Test that all expected emoji prefixes are defined."""
        assert OutputLevel.INFO in EMOJI_PREFIXES
        assert OutputLevel.SUCCESS in EMOJI_PREFIXES
        assert OutputLevel.WARNING in EMOJI_PREFIXES
        assert OutputLevel.ERROR in EMOJI_PREFIXES
        assert OutputLevel.DEBUG in EMOJI_PREFIXES

    def test_emoji_prefixes_are_strings(self):
        """Test that emoji prefixes are strings."""
        for level, emoji in EMOJI_PREFIXES.items():
            assert isinstance(emoji, str), f"Emoji for {level} should be string"


class TestDomainEmojis:
    """Tests for domain-specific emoji constants."""

    def test_domain_emojis_exist(self):
        """Test that common domain emojis are defined."""
        expected_keys = [
            "email",
            "download",
            "upload",
            "file",
            "folder",
            "processing",
            "complete",
            "url",
        ]
        for key in expected_keys:
            assert key in DOMAIN_EMOJIS, f"Missing domain emoji: {key}"

    def test_domain_emojis_are_strings(self):
        """Test that domain emojis are strings."""
        for key, emoji in DOMAIN_EMOJIS.items():
            assert isinstance(emoji, str), f"Emoji for {key} should be string"


class TestEmit:
    """Tests for emit function."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_info_message(self, mock_stdout):
        """Test emitting an info message."""
        emit("Test message", OutputLevel.INFO)
        output = mock_stdout.getvalue()
        assert "Test message" in output
        assert EMOJI_PREFIXES[OutputLevel.INFO] in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_success_message(self, mock_stdout):
        """Test emitting a success message."""
        emit("Operation successful", OutputLevel.SUCCESS)
        output = mock_stdout.getvalue()
        assert "Operation successful" in output
        assert EMOJI_PREFIXES[OutputLevel.SUCCESS] in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_error_message(self, mock_stdout):
        """Test emitting an error message."""
        emit("Something failed", OutputLevel.ERROR)
        output = mock_stdout.getvalue()
        assert "Something failed" in output
        assert EMOJI_PREFIXES[OutputLevel.ERROR] in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_with_indent(self, mock_stdout):
        """Test emitting with indentation."""
        emit("Indented message", OutputLevel.INFO, indent=4)
        output = mock_stdout.getvalue()
        assert "    " in output  # 4 spaces
        assert "Indented message" in output


class TestEmitWithEmoji:
    """Tests for emit_with_emoji function."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_with_valid_emoji_key(self, mock_stdout):
        """Test emitting with a valid emoji key."""
        emit_with_emoji("Downloading file", "download")
        output = mock_stdout.getvalue()
        assert "Downloading file" in output
        assert DOMAIN_EMOJIS["download"] in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_with_unknown_emoji_key(self, mock_stdout):
        """Test emitting with unknown emoji key falls back to bullet."""
        emit_with_emoji("Unknown domain", "nonexistent_key")
        output = mock_stdout.getvalue()
        assert "Unknown domain" in output
        assert "•" in output  # fallback bullet

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_with_emoji_and_indent(self, mock_stdout):
        """Test emit_with_emoji with indentation."""
        emit_with_emoji("Processing data", "processing", indent=2)
        output = mock_stdout.getvalue()
        assert "  " in output  # 2 spaces indent
        assert "Processing data" in output


class TestEmitHeader:
    """Tests for emit_header function."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_header_default(self, mock_stdout):
        """Test emitting a header with default settings."""
        emit_header("Section Title")
        output = mock_stdout.getvalue()
        assert "Section Title" in output
        assert "=" * 60 in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_header_custom_char(self, mock_stdout):
        """Test emitting a header with custom character."""
        emit_header("Custom Header", char="-")
        output = mock_stdout.getvalue()
        assert "Custom Header" in output
        assert "-" * 60 in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_header_custom_width(self, mock_stdout):
        """Test emitting a header with custom width."""
        emit_header("Narrow Header", char="=", width=40)
        output = mock_stdout.getvalue()
        assert "Narrow Header" in output
        assert "=" * 40 in output


class TestEmitSeparator:
    """Tests for emit_separator function."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_separator_default(self, mock_stdout):
        """Test emitting a separator with default settings."""
        emit_separator()
        output = mock_stdout.getvalue()
        assert "=" * 60 in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_separator_custom(self, mock_stdout):
        """Test emitting a custom separator."""
        emit_separator(char="-", width=40)
        output = mock_stdout.getvalue()
        assert "-" * 40 in output


class TestEmitList:
    """Tests for emit_list function."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_list_unnumbered(self, mock_stdout):
        """Test emitting an unnumbered list."""
        emit_list(["item1", "item2", "item3"])
        output = mock_stdout.getvalue()
        assert "item1" in output
        assert "item2" in output
        assert "item3" in output
        assert "•" in output  # bullet points

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_list_numbered(self, mock_stdout):
        """Test emitting a numbered list."""
        emit_list(["first", "second", "third"], numbered=True)
        output = mock_stdout.getvalue()
        assert "1." in output
        assert "2." in output
        assert "3." in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_list_with_indent(self, mock_stdout):
        """Test emitting a list with indentation."""
        emit_list(["indented"], indent=4)
        output = mock_stdout.getvalue()
        assert "    " in output  # 4 spaces

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_list_empty(self, mock_stdout):
        """Test emitting an empty list."""
        emit_list([])
        output = mock_stdout.getvalue()
        assert output == ""


class TestEmitKeyValue:
    """Tests for emit_key_value function."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_key_value_basic(self, mock_stdout):
        """Test emitting key-value pairs."""
        emit_key_value({"name": "test", "value": 42})
        output = mock_stdout.getvalue()
        assert "name: test" in output
        assert "value: 42" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_key_value_with_indent(self, mock_stdout):
        """Test emitting key-value pairs with indentation."""
        emit_key_value({"key": "value"}, indent=2)
        output = mock_stdout.getvalue()
        assert "  key: value" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_key_value_empty(self, mock_stdout):
        """Test emitting empty dictionary."""
        emit_key_value({})
        output = mock_stdout.getvalue()
        assert output == ""


class TestConvenienceFunctions:
    """Tests for convenience output functions."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_info(self, mock_stdout):
        """Test info convenience function."""
        info("Info message")
        assert "Info message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_success(self, mock_stdout):
        """Test success convenience function."""
        success("Success message")
        assert "Success message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_warning(self, mock_stdout):
        """Test warning convenience function."""
        warning("Warning message")
        assert "Warning message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_error(self, mock_stdout):
        """Test error convenience function."""
        error("Error message")
        assert "Error message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_debug(self, mock_stdout):
        """Test debug convenience function."""
        debug("Debug message")
        assert "Debug message" in mock_stdout.getvalue()


class TestDomainConvenienceFunctions:
    """Tests for domain-specific convenience functions."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_processing(self, mock_stdout):
        """Test processing convenience function."""
        processing("Processing data...")
        assert "Processing data..." in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_complete(self, mock_stdout):
        """Test complete convenience function."""
        complete()
        assert "Complete!" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_complete_custom_message(self, mock_stdout):
        """Test complete with custom message."""
        complete("All done!")
        assert "All done!" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_downloading(self, mock_stdout):
        """Test downloading convenience function."""
        downloading("Downloading file.pdf")
        assert "Downloading file.pdf" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_converting(self, mock_stdout):
        """Test converting convenience function."""
        converting("Converting PDF to markdown")
        assert "Converting PDF to markdown" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_date_info(self, mock_stdout):
        """Test date_info convenience function."""
        date_info("Study date: 2024-06-04")
        assert "Study date: 2024-06-04" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_url_info(self, mock_stdout):
        """Test url_info convenience function."""
        url_info("https://example.com")
        assert "https://example.com" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_file_info(self, mock_stdout):
        """Test file_info convenience function."""
        file_info("report.pdf")
        assert "report.pdf" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_folder_info(self, mock_stdout):
        """Test folder_info convenience function."""
        folder_info("medical_data/")
        assert "medical_data/" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_size_info(self, mock_stdout):
        """Test size_info convenience function."""
        size_info("1.5 MB")
        assert "1.5 MB" in mock_stdout.getvalue()


class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_format_bytes_bytes(self):
        """Test formatting small byte values."""
        assert format_bytes(0) == "0.0 B"
        assert format_bytes(512) == "512.0 B"
        assert format_bytes(1023) == "1023.0 B"

    def test_format_bytes_kilobytes(self):
        """Test formatting kilobyte values."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1536) == "1.5 KB"
        assert format_bytes(10240) == "10.0 KB"

    def test_format_bytes_megabytes(self):
        """Test formatting megabyte values."""
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(1572864) == "1.5 MB"
        assert format_bytes(10485760) == "10.0 MB"

    def test_format_bytes_gigabytes(self):
        """Test formatting gigabyte values."""
        assert format_bytes(1073741824) == "1.0 GB"
        assert format_bytes(1610612736) == "1.5 GB"

    def test_format_bytes_terabytes(self):
        """Test formatting terabyte values."""
        assert format_bytes(1099511627776) == "1.0 TB"
        assert format_bytes(1649267441664) == "1.5 TB"


class TestEmitFileSaved:
    """Tests for emit_file_saved function."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_file_saved_basic(self, mock_stdout):
        """Test emitting file saved message."""
        emit_file_saved("/path/to/file.pdf", 1048576)  # 1 MB
        output = mock_stdout.getvalue()
        assert "/path/to/file.pdf" in output
        assert "1.0 MB" in output
        assert "Saved:" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_file_saved_with_indent(self, mock_stdout):
        """Test emitting file saved with indentation."""
        emit_file_saved("file.pdf", 512, indent=2)
        output = mock_stdout.getvalue()
        assert "  " in output  # 2 space indent

    @patch("sys.stdout", new_callable=StringIO)
    def test_emit_file_saved_small_file(self, mock_stdout):
        """Test emitting small file saved message."""
        emit_file_saved("small.txt", 256)
        output = mock_stdout.getvalue()
        assert "256.0 B" in output
