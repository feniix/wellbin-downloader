"""
Output utilities for wellbin CLI.

Provides structured output functions for consistent CLI messaging across the codebase.
"""

from enum import Enum
from typing import Any


class OutputLevel(Enum):
    """Output severity levels."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


# Emoji prefixes for different message types
EMOJI_PREFIXES = {
    OutputLevel.INFO: "ℹ️",
    OutputLevel.SUCCESS: "✅",
    OutputLevel.WARNING: "⚠️",
    OutputLevel.ERROR: "❌",
    OutputLevel.DEBUG: "🔍",
}

# Domain-specific emoji prefixes
DOMAIN_EMOJIS = {
    "email": "📧",
    "password": "🔐",
    "login": "🚀",
    "logout": "🔒",
    "download": "📥",
    "upload": "📤",
    "file": "📄",
    "folder": "📁",
    "search": "🔎",
    "filter": "🎯",
    "limit": "🔢",
    "date": "📅",
    "time": "⏰",
    "browser": "🌐",
    "driver": "🔧",
    "conversion": "🔄",
    "processing": "⚙️",
    "complete": "🎉",
    "config": "🔧",
    "argument": "🔧",
    "mode": "🤖",
    "url": "🔗",
    "status": "📊",
    "size": "💾",
    "line": "=",
}


def emit(message: str, level: OutputLevel = OutputLevel.INFO, indent: int = 0) -> None:
    """Emit a formatted message to stdout.

    Args:
        message: The message to emit
        level: Output level (determines emoji prefix)
        indent: Number of spaces to indent
    """
    prefix = " " * indent + EMOJI_PREFIXES.get(level, "")
    print(f"{prefix} {message}")


def emit_with_emoji(message: str, emoji_key: str, indent: int = 0) -> None:
    """Emit a message with a domain-specific emoji.

    Args:
        message: The message to emit
        emoji_key: Key from DOMAIN_EMOJIS dict
        indent: Number of spaces to indent
    """
    emoji = DOMAIN_EMOJIS.get(emoji_key, "•")
    prefix = " " * indent
    print(f"{prefix}{emoji} {message}")


def emit_header(title: str, char: str = "=", width: int = 60) -> None:
    """Emit a section header.

    Args:
        title: Header title
        char: Character to use for separator line
        width: Width of separator line
    """
    print(title)
    print(char * width)


def emit_separator(char: str = "=", width: int = 60) -> None:
    """Emit a separator line.

    Args:
        char: Character to use for separator
        width: Width of separator line
    """
    print(char * width)


def emit_list(items: list[Any], indent: int = 2, numbered: bool = False) -> None:
    """Emit a list of items.

    Args:
        items: List of items to display
        indent: Indentation level
        numbered: Whether to number the items
    """
    prefix = " " * indent
    for i, item in enumerate(items, 1):
        if numbered:
            print(f"{prefix}{i}. {item}")
        else:
            print(f"{prefix}• {item}")


def emit_key_value(data: dict[str, Any], indent: int = 0) -> None:
    """Emit a dictionary as key-value pairs.

    Args:
        data: Dictionary to display
        indent: Indentation level
    """
    prefix = " " * indent
    for key, value in data.items():
        print(f"{prefix}{key}: {value}")


# Convenience functions for common patterns
def info(message: str, indent: int = 0) -> None:
    """Emit an info message."""
    emit(message, OutputLevel.INFO, indent)


def success(message: str, indent: int = 0) -> None:
    """Emit a success message."""
    emit(message, OutputLevel.SUCCESS, indent)


def warning(message: str, indent: int = 0) -> None:
    """Emit a warning message."""
    emit(message, OutputLevel.WARNING, indent)


def error(message: str, indent: int = 0) -> None:
    """Emit an error message."""
    emit(message, OutputLevel.ERROR, indent)


def debug(message: str, indent: int = 0) -> None:
    """Emit a debug message."""
    emit(message, OutputLevel.DEBUG, indent)


# Domain-specific convenience functions
def processing(message: str, indent: int = 0) -> None:
    """Emit a processing message."""
    emit_with_emoji(message, "processing", indent)


def complete(message: str = "Complete!", indent: int = 0) -> None:
    """Emit a completion message."""
    emit_with_emoji(message, "complete", indent)


def downloading(message: str, indent: int = 0) -> None:
    """Emit a download message."""
    emit_with_emoji(message, "download", indent)


def converting(message: str, indent: int = 0) -> None:
    """Emit a conversion message."""
    emit_with_emoji(message, "conversion", indent)


def date_info(message: str, indent: int = 0) -> None:
    """Emit a date-related message."""
    emit_with_emoji(message, "date", indent)


def url_info(message: str, indent: int = 0) -> None:
    """Emit a URL-related message."""
    emit_with_emoji(message, "url", indent)


def file_info(message: str, indent: int = 0) -> None:
    """Emit a file-related message."""
    emit_with_emoji(message, "file", indent)


def folder_info(message: str, indent: int = 0) -> None:
    """Emit a folder-related message."""
    emit_with_emoji(message, "folder", indent)


def size_info(message: str, indent: int = 0) -> None:
    """Emit a size-related message."""
    emit_with_emoji(message, "size", indent)


def format_bytes(size: int) -> str:
    """Format byte size as human-readable string.

    Args:
        size: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    float_size: float = float(size)
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(float_size) < 1024.0:
            return f"{float_size:.1f} {unit}"
        float_size /= 1024.0
    return f"{float_size:.1f} TB"


def emit_file_saved(path: str, size: int, indent: int = 0) -> None:
    """Emit a file saved message with size.

    Args:
        path: File path
        size: File size in bytes
        indent: Indentation level
    """
    prefix = " " * indent
    size_str = format_bytes(size)
    print(f"{prefix}✅ Saved: {path} ({size_str})")
