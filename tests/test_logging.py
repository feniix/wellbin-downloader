"""
Tests for wellbin.core.logging module.
"""

import logging
from io import StringIO
from unittest.mock import patch

import pytest

from wellbin.core.logging import (
    LogLevel,
    Output,
    OutputConfig,
    configure_output,
    debug,
    error,
    get_output,
    header,
    info,
    log,
    progress,
    reset_output,
    separator,
    success,
    warning,
)


@pytest.fixture(autouse=True)
def _reset_global_output():
    """Reset global output singleton before each test."""
    reset_output()
    yield
    reset_output()


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_log_level_values(self):
        """Test that LogLevel has emoji values."""
        assert LogLevel.DEBUG.value == "\U0001f50d"
        assert LogLevel.SUCCESS.value == "\u2705"
        assert LogLevel.ERROR.value == "\u274c"
        assert LogLevel.WARNING.value == "\u26a0\ufe0f"
        assert LogLevel.INFO.value == "\u2139\ufe0f"
        assert LogLevel.PROGRESS.value == "\U0001f4ca"
        assert LogLevel.ACTION.value == "\U0001f3af"

    def test_log_level_count(self):
        """Test that all expected log levels exist."""
        assert len(LogLevel) == 7


class TestOutputConfig:
    """Tests for OutputConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OutputConfig()
        assert config.use_colors is True
        assert config.use_emoji is True
        assert config.indent_size == 2
        assert config.line_width == 60

    def test_custom_config(self):
        """Test custom configuration."""
        config = OutputConfig(use_emoji=False, indent_size=4, line_width=80)
        assert config.use_emoji is False
        assert config.indent_size == 4
        assert config.line_width == 80


class TestOutputInit:
    """Tests for Output initialization."""

    def test_default_init(self):
        """Test Output with default config."""
        out = Output()
        assert out.config.use_emoji is True
        assert out._indent_level == 0
        assert out._logger is None

    def test_custom_config_init(self):
        """Test Output with custom config."""
        config = OutputConfig(use_emoji=False, line_width=80)
        out = Output(config)
        assert out.config.use_emoji is False
        assert out.config.line_width == 80


class TestOutputMessage:
    """Tests for Output.message() method."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_message_info(self, mock_stdout):
        """Test info level message output."""
        out = Output()
        out.message(LogLevel.INFO, "Hello world")
        output = mock_stdout.getvalue()
        assert "Hello world" in output
        assert LogLevel.INFO.value in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_message_success(self, mock_stdout):
        """Test success level message output."""
        out = Output()
        out.message(LogLevel.SUCCESS, "Done")
        output = mock_stdout.getvalue()
        assert "Done" in output
        assert LogLevel.SUCCESS.value in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_message_error(self, mock_stdout):
        """Test error level message output."""
        out = Output()
        out.message(LogLevel.ERROR, "Failed")
        output = mock_stdout.getvalue()
        assert "Failed" in output
        assert LogLevel.ERROR.value in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_message_warning(self, mock_stdout):
        """Test warning level message output."""
        out = Output()
        out.message(LogLevel.WARNING, "Watch out")
        output = mock_stdout.getvalue()
        assert "Watch out" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_message_with_kwargs_format(self, mock_stdout):
        """Test message with format kwargs."""
        out = Output()
        out.message(LogLevel.INFO, "Hello {name}", name="World")
        assert "Hello World" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_message_no_emoji(self, mock_stdout):
        """Test message with emoji disabled."""
        config = OutputConfig(use_emoji=False)
        out = Output(config)
        out.message(LogLevel.SUCCESS, "No emoji here")
        output = mock_stdout.getvalue()
        assert "No emoji here" in output
        assert LogLevel.SUCCESS.value not in output


class TestOutputLog:
    """Tests for Output.log() method."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_log_with_emoji(self, mock_stdout):
        """Test log with custom emoji."""
        out = Output()
        out.log("\U0001f4c5", "Study date: 2024-06-04")
        output = mock_stdout.getvalue()
        assert "\U0001f4c5" in output
        assert "Study date: 2024-06-04" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_log_with_empty_emoji(self, mock_stdout):
        """Test log with empty emoji string."""
        out = Output()
        out.log("", "No emoji prefix")
        output = mock_stdout.getvalue()
        assert "No emoji prefix" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_log_no_emoji_config(self, mock_stdout):
        """Test log with emoji disabled in config."""
        config = OutputConfig(use_emoji=False)
        out = Output(config)
        out.log("\U0001f4c5", "Date info")
        output = mock_stdout.getvalue()
        assert "Date info" in output
        assert "\U0001f4c5" not in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_log_with_kwargs(self, mock_stdout):
        """Test log with format kwargs."""
        out = Output()
        out.log("\U0001f517", "URL: {url}", url="https://example.com")
        assert "URL: https://example.com" in mock_stdout.getvalue()


class TestOutputStep:
    """Tests for Output.step() method."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_step_format(self, mock_stdout):
        """Test step progress format."""
        out = Output()
        out.step(1, 5, "\U0001f4c4", "Processing study...")
        output = mock_stdout.getvalue()
        assert "[1/5]" in output
        assert "\U0001f4c4" in output
        assert "Processing study..." in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_step_no_emoji(self, mock_stdout):
        """Test step with emoji disabled."""
        config = OutputConfig(use_emoji=False)
        out = Output(config)
        out.step(3, 10, "\U0001f4c4", "Processing")
        output = mock_stdout.getvalue()
        assert "[3/10]" in output
        assert "Processing" in output
        assert "\U0001f4c4" not in output


class TestOutputTraceback:
    """Tests for Output.traceback() method."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_traceback_output(self, mock_stdout):
        """Test traceback prints exception info."""
        out = Output()
        try:
            raise ValueError("test error")
        except ValueError:
            out.traceback()
        output = mock_stdout.getvalue()
        assert "ValueError" in output
        assert "test error" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_traceback_with_logger(self, mock_stdout):
        """Test traceback logs to logger at ERROR level."""
        out = Output()
        out.configure_logging("test_tb", logging.DEBUG)
        try:
            raise RuntimeError("logged error")
        except RuntimeError:
            out.traceback()
        output = mock_stdout.getvalue()
        assert "RuntimeError" in output


class TestOutputIndent:
    """Tests for indent/dedent state management."""

    def test_indent_increases_level(self):
        """Test that indent increases the indent level."""
        out = Output()
        assert out._indent_level == 0
        out.indent()
        assert out._indent_level == 1
        out.indent()
        assert out._indent_level == 2

    def test_dedent_decreases_level(self):
        """Test that dedent decreases the indent level."""
        out = Output()
        out.indent()
        out.indent()
        out.dedent()
        assert out._indent_level == 1

    def test_dedent_at_zero(self):
        """Test that dedent at zero doesn't go negative."""
        out = Output()
        out.dedent()  # Should not raise
        assert out._indent_level == 0

    def test_indent_string_generation(self):
        """Test that _indent() returns correct spacing."""
        out = Output()
        assert out._indent() == ""
        out.indent()
        assert out._indent() == "  "  # 2 spaces (default)
        out.indent()
        assert out._indent() == "    "  # 4 spaces

    def test_custom_indent_size(self):
        """Test custom indent size in _indent()."""
        config = OutputConfig(indent_size=4)
        out = Output(config)
        out.indent()
        assert out._indent() == "    "  # 4 spaces


class TestOutputHeader:
    """Tests for Output.header() method."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_header_default(self, mock_stdout):
        """Test header with default character."""
        out = Output()
        out.header("Test Header")
        output = mock_stdout.getvalue()
        assert "Test Header" in output
        assert "=" * 60 in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_header_custom_char(self, mock_stdout):
        """Test header with custom character."""
        out = Output()
        out.header("Custom", char="-")
        output = mock_stdout.getvalue()
        assert "-" * 60 in output


class TestOutputSeparator:
    """Tests for Output.separator() method."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_separator_default(self, mock_stdout):
        """Test separator with default character."""
        out = Output()
        out.separator()
        assert "=" * 60 in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_separator_custom(self, mock_stdout):
        """Test separator with custom character."""
        out = Output()
        out.separator(char="-")
        assert "-" * 60 in mock_stdout.getvalue()


class TestOutputItem:
    """Tests for Output.item() and subitem() methods."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_item_bullet(self, mock_stdout):
        """Test bullet point item."""
        out = Output()
        out.item("List item")
        output = mock_stdout.getvalue()
        assert "\u2022" in output
        assert "List item" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_item_numbered(self, mock_stdout):
        """Test numbered item."""
        out = Output()
        out.item("Numbered item", index=3)
        output = mock_stdout.getvalue()
        assert "3." in output
        assert "Numbered item" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_subitem(self, mock_stdout):
        """Test sub-item output."""
        out = Output()
        out.subitem("Sub detail")
        assert "Sub detail" in mock_stdout.getvalue()


class TestOutputConvenienceMethods:
    """Tests for convenience methods (info, success, error, etc.)."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_info(self, mock_stdout):
        """Test info convenience method."""
        out = Output()
        out.info("Info message")
        assert "Info message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_success(self, mock_stdout):
        """Test success convenience method."""
        out = Output()
        out.success("Success message")
        assert "Success message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_error(self, mock_stdout):
        """Test error convenience method."""
        out = Output()
        out.error("Error message")
        assert "Error message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_warning(self, mock_stdout):
        """Test warning convenience method."""
        out = Output()
        out.warning("Warning message")
        assert "Warning message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_debug(self, mock_stdout):
        """Test debug convenience method."""
        out = Output()
        out.debug("Debug message")
        assert "Debug message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_progress(self, mock_stdout):
        """Test progress convenience method."""
        out = Output()
        out.progress("Progress message")
        assert "Progress message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_action(self, mock_stdout):
        """Test action convenience method."""
        out = Output()
        out.action("Action message")
        assert "Action message" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_blank(self, mock_stdout):
        """Test blank line output."""
        out = Output()
        out.blank()
        assert mock_stdout.getvalue() == "\n"

    @patch("sys.stdout", new_callable=StringIO)
    def test_section(self, mock_stdout):
        """Test section output (blank + action)."""
        out = Output()
        out.section("Section Title")
        output = mock_stdout.getvalue()
        assert "Section Title" in output


class TestOutputLogging:
    """Tests for Python logging integration."""

    def test_configure_logging(self):
        """Test configuring Python logger."""
        out = Output()
        out.configure_logging("test_logger", logging.DEBUG)
        assert out._logger is not None
        assert out._logger.name == "test_logger"
        assert out._logger.level == logging.DEBUG

    def test_configure_logging_adds_handler(self):
        """Test that configure_logging adds a handler."""
        out = Output()
        # Use a unique name to avoid handler accumulation
        out.configure_logging("test_handler_add", logging.INFO)
        assert len(out._logger.handlers) == 1

    @patch("sys.stdout", new_callable=StringIO)
    def test_message_logs_to_logger(self, mock_stdout):
        """Test that message() also logs to Python logger."""
        out = Output()
        out.configure_logging("test_msg_log", logging.DEBUG)
        out.message(LogLevel.ERROR, "error logged")
        # Output should appear (both print and logger write to stdout)
        assert "error logged" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_log_method_logs_to_logger(self, mock_stdout):
        """Test that log() method also logs to Python logger."""
        out = Output()
        out.configure_logging("test_log_log", logging.DEBUG)
        out.log("\U0001f4c5", "date info")
        assert "date info" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_header_logs_to_logger(self, mock_stdout):
        """Test that header() logs to Python logger."""
        out = Output()
        out.configure_logging("test_hdr_log", logging.DEBUG)
        out.header("Header Text")
        assert "Header Text" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_separator_logs_to_logger(self, mock_stdout):
        """Test that separator() logs to Python logger."""
        out = Output()
        out.configure_logging("test_sep_log", logging.DEBUG)
        out.separator()
        assert "=" * 60 in mock_stdout.getvalue()


class TestGetOutput:
    """Tests for get_output() singleton."""

    def test_returns_output_instance(self):
        """Test that get_output returns an Output instance."""
        out = get_output()
        assert isinstance(out, Output)

    def test_singleton_behavior(self):
        """Test that get_output returns same instance."""
        out1 = get_output()
        out2 = get_output()
        assert out1 is out2

    def test_reset_creates_new_instance(self):
        """Test that reset_output clears the singleton."""
        out1 = get_output()
        reset_output()
        out2 = get_output()
        assert out1 is not out2


class TestConfigureOutput:
    """Tests for configure_output() function."""

    def test_configure_with_custom_config(self):
        """Test configuring global output with custom config."""
        config = OutputConfig(use_emoji=False, line_width=80)
        out = configure_output(config)
        assert out.config.use_emoji is False
        assert out.config.line_width == 80

    def test_configure_replaces_singleton(self):
        """Test that configure_output replaces the global instance."""
        original = get_output()
        new = configure_output(OutputConfig(line_width=100))
        assert new is not original
        assert get_output() is new

    def test_configure_with_none(self):
        """Test configuring with None creates default config."""
        out = configure_output(None)
        assert out.config.use_emoji is True
        assert out.config.line_width == 60


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_info_function(self, mock_stdout):
        """Test module-level info function."""
        info("Module info")
        assert "Module info" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_success_function(self, mock_stdout):
        """Test module-level success function."""
        success("Module success")
        assert "Module success" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_warning_function(self, mock_stdout):
        """Test module-level warning function."""
        warning("Module warning")
        assert "Module warning" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_error_function(self, mock_stdout):
        """Test module-level error function."""
        error("Module error")
        assert "Module error" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_debug_function(self, mock_stdout):
        """Test module-level debug function."""
        debug("Module debug")
        assert "Module debug" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_progress_function(self, mock_stdout):
        """Test module-level progress function."""
        progress("Module progress")
        assert "Module progress" in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_log_function(self, mock_stdout):
        """Test module-level log function."""
        log("\U0001f4c5", "Module log")
        output = mock_stdout.getvalue()
        assert "\U0001f4c5" in output
        assert "Module log" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_header_function(self, mock_stdout):
        """Test module-level header function."""
        header("Module Header")
        output = mock_stdout.getvalue()
        assert "Module Header" in output
        assert "=" * 60 in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_separator_function(self, mock_stdout):
        """Test module-level separator function."""
        separator()
        assert "=" * 60 in mock_stdout.getvalue()

    @patch("sys.stdout", new_callable=StringIO)
    def test_separator_custom_char(self, mock_stdout):
        """Test module-level separator with custom char."""
        separator(char="-")
        assert "-" * 60 in mock_stdout.getvalue()
