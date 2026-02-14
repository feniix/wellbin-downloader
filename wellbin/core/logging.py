"""
Centralized logging and output utilities for Wellbin.

Provides consistent output formatting with emoji indicators and
optional logging integration.
"""

import logging
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class LogLevel(Enum):
    """Log levels with emoji indicators."""

    DEBUG = "🔍"
    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    PROGRESS = "📊"
    ACTION = "🎯"


@dataclass
class OutputConfig:
    """Configuration for output formatting."""

    use_colors: bool = True
    use_emoji: bool = True
    indent_size: int = 2
    line_width: int = 60


class Output:
    """Centralized output handler with consistent formatting.

    Provides a unified interface for all output in the Wellbin application.
    Supports both console output and Python logging integration.
    """

    def __init__(self, config: Optional[OutputConfig] = None):
        """Initialize output handler.

        Args:
            config: Output configuration options
        """
        self.config = config or OutputConfig()
        self._indent_level = 0
        self._logger: Optional[logging.Logger] = None

    def configure_logging(self, name: str = "wellbin", level: int = logging.INFO) -> None:
        """Configure Python logging integration.

        Args:
            name: Logger name
            level: Logging level
        """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def _get_emoji(self, level: LogLevel) -> str:
        """Get emoji for log level.

        Args:
            level: Log level

        Returns:
            Emoji string or empty if disabled
        """
        if not self.config.use_emoji:
            return ""
        return level.value

    def _indent(self) -> str:
        """Get current indentation string.

        Returns:
            Indentation string
        """
        return " " * (self._indent_level * self.config.indent_size)

    def indent(self) -> None:
        """Increase indentation level."""
        self._indent_level += 1

    def dedent(self) -> None:
        """Decrease indentation level."""
        if self._indent_level > 0:
            self._indent_level -= 1

    def message(self, level: LogLevel, text: str, **kwargs: Any) -> None:
        """Print a formatted message.

        Args:
            level: Log level
            text: Message text
            **kwargs: Additional format arguments
        """
        emoji = self._get_emoji(level)
        formatted = text.format(**kwargs) if kwargs else text
        output = f"{self._indent()}{emoji} {formatted}".strip()

        print(output)

        if self._logger:
            self._logger.log(logging.INFO if level in (LogLevel.INFO, LogLevel.SUCCESS) else logging.WARNING, output)

    def info(self, text: str, **kwargs: Any) -> None:
        """Print info message."""
        self.message(LogLevel.INFO, text, **kwargs)

    def success(self, text: str, **kwargs: Any) -> None:
        """Print success message."""
        self.message(LogLevel.SUCCESS, text, **kwargs)

    def warning(self, text: str, **kwargs: Any) -> None:
        """Print warning message."""
        self.message(LogLevel.WARNING, text, **kwargs)

    def error(self, text: str, **kwargs: Any) -> None:
        """Print error message."""
        self.message(LogLevel.ERROR, text, **kwargs)

    def debug(self, text: str, **kwargs: Any) -> None:
        """Print debug message."""
        self.message(LogLevel.DEBUG, text, **kwargs)

    def progress(self, text: str, **kwargs: Any) -> None:
        """Print progress message."""
        self.message(LogLevel.PROGRESS, text, **kwargs)

    def action(self, text: str, **kwargs: Any) -> None:
        """Print action message."""
        self.message(LogLevel.ACTION, text, **kwargs)

    def header(self, text: str, char: str = "=") -> None:
        """Print a header with separator line.

        Args:
            text: Header text
            char: Character for separator line
        """
        print(f"\n{char * self.config.line_width}")
        print(text)
        print(char * self.config.line_width)

    def separator(self, char: str = "=") -> None:
        """Print a separator line.

        Args:
            char: Character for separator
        """
        print(char * self.config.line_width)

    def blank(self) -> None:
        """Print blank line."""
        print()

    def section(self, title: str) -> None:
        """Print section header.

        Args:
            title: Section title
        """
        self.blank()
        self.action(title)

    def item(self, text: str, index: Optional[int] = None, **kwargs: Any) -> None:
        """Print list item.

        Args:
            text: Item text
            index: Optional item number
            **kwargs: Additional format arguments
        """
        formatted = text.format(**kwargs) if kwargs else text
        if index is not None:
            print(f"{self._indent()}  {index}. {formatted}")
        else:
            print(f"{self._indent()}  • {formatted}")

    def subitem(self, text: str, **kwargs: Any) -> None:
        """Print sub-item (additional indented item).

        Args:
            text: Sub-item text
            **kwargs: Additional format arguments
        """
        formatted = text.format(**kwargs) if kwargs else text
        print(f"{self._indent()}     {formatted}")


# Global output instance
_output: Optional[Output] = None


def get_output() -> Output:
    """Get global output instance.

    Returns:
        Global Output instance
    """
    global _output
    if _output is None:
        _output = Output()
    return _output


def configure_output(config: Optional[OutputConfig] = None) -> Output:
    """Configure global output instance.

    Args:
        config: Output configuration

    Returns:
        Configured Output instance
    """
    global _output
    _output = Output(config)
    return _output


# Convenience functions using global instance
def info(text: str, **kwargs: Any) -> None:
    """Print info message using global output."""
    get_output().info(text, **kwargs)


def success(text: str, **kwargs: Any) -> None:
    """Print success message using global output."""
    get_output().success(text, **kwargs)


def warning(text: str, **kwargs: Any) -> None:
    """Print warning message using global output."""
    get_output().warning(text, **kwargs)


def error(text: str, **kwargs: Any) -> None:
    """Print error message using global output."""
    get_output().error(text, **kwargs)


def debug(text: str, **kwargs: Any) -> None:
    """Print debug message using global output."""
    get_output().debug(text, **kwargs)


def progress(text: str, **kwargs: Any) -> None:
    """Print progress message using global output."""
    get_output().progress(text, **kwargs)


def header(text: str, char: str = "=") -> None:
    """Print header using global output."""
    get_output().header(text, char)


def separator(char: str = "=") -> None:
    """Print separator using global output."""
    get_output().separator(char)
