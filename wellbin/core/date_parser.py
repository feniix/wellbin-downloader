"""
Date parsing utilities for the Wellbin Medical Data Downloader.

This module provides sophisticated date extraction with multiple fallback patterns,
optimized for medical document formats with LRU caching for performance.
"""

import re
from functools import lru_cache
from typing import Final

# Date parsing patterns in order of preference
DATE_PATTERNS: Final[list[str]] = [
    r"(\d{1,2})/(\d{1,2})/(\d{4})",  # MM/DD/YYYY or DD/MM/YYYY
    r"(\d{4})/(\d{1,2})/(\d{1,2})",  # YYYY/MM/DD
    r"(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})",  # DD Mon YYYY
    r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})",  # Mon DD, YYYY
]

# Month name to number mapping (supports English and Spanish)
MONTH_MAP: Final[dict[str, str]] = {
    # English
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
    # Spanish (only unique ones)
    "ene": "01",
    "abr": "04",
    "ago": "08",
    "sept": "09",
    "dic": "12",
}

# Default fallback date when no date found
DEFAULT_FALLBACK_DATE: Final[str] = "20240101"


@lru_cache(maxsize=1024)
def is_valid_date(year: int, month: int, day: int) -> bool:
    """Validate that date components form a valid calendar date.

    Args:
        year: Year (1900-2099)
        month: Month (1-12)
        day: Day of month

    Returns:
        True if the date is valid, False otherwise

    Examples:
        >>> is_valid_date(2024, 2, 29)  # Leap year
        True
        >>> is_valid_date(2023, 2, 29)  # Not a leap year
        False
    """
    if not (1900 <= year <= 2099):
        return False
    if not (1 <= month <= 12):
        return False

    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    # Handle leap years
    if month == 2 and ((year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)):
        max_day = 29
    else:
        max_day = days_in_month[month - 1]

    return 1 <= day <= max_day


def _parse_ambiguous_date(match: tuple[str, ...]) -> str | None:
    """Parse ambiguous DD/MM vs MM/DD format.

    Uses heuristics to determine format when either interpretation is possible.

    Args:
        match: Tuple of (part1, part2, year) strings

    Returns:
        Date string in YYYYMMDD format, or None if invalid
    """
    part1, part2, year = match
    part1_int, part2_int, year_int = int(part1), int(part2), int(year)

    # Try to determine format based on values
    if part1_int > 12:  # Must be DD/MM/YYYY (day > 12)
        day, month = part1_int, part2_int
    elif part2_int > 12:  # Must be MM/DD/YYYY (day > 12)
        month, day = part1_int, part2_int
    else:  # Ambiguous - assume DD/MM/YYYY (European format)
        day, month = part1_int, part2_int

    if is_valid_date(year_int, month, day):
        return f"{year_int}{month:02d}{day:02d}"
    return None


def _parse_iso_date(match: tuple[str, ...]) -> str | None:
    """Parse YYYY/MM/DD format.

    Args:
        match: Tuple of (year, month, day) strings

    Returns:
        Date string in YYYYMMDD format, or None if invalid
    """
    year_str, month_str, day_str = match
    year_int, month_int, day_int = int(year_str), int(month_str), int(day_str)
    if is_valid_date(year_int, month_int, day_int):
        return f"{year_int}{month_int:02d}{day_int:02d}"
    return None


def _parse_day_month_year_date(match: tuple[str, ...], month_map: dict[str, str]) -> str | None:
    """Parse DD Mon YYYY format.

    Args:
        match: Tuple of (day, month_name, year) strings
        month_map: Month name to number mapping

    Returns:
        Date string in YYYYMMDD format, or None if invalid
    """
    day_str, month_name, year_str = match
    day_int, year_int = int(day_str), int(year_str)
    month_int = int(month_map.get(month_name.lower()[:3], "01"))
    if is_valid_date(year_int, month_int, day_int):
        return f"{year_int}{month_int:02d}{day_int:02d}"
    return None


def _parse_month_day_year_date(match: tuple[str, ...], month_map: dict[str, str]) -> str | None:
    """Parse Mon DD, YYYY format.

    Args:
        match: Tuple of (month_name, day, year) strings
        month_map: Month name to number mapping

    Returns:
        Date string in YYYYMMDD format, or None if invalid
    """
    month_name, day_str, year_str = match
    day_int, year_int = int(day_str), int(year_str)
    month_int = int(month_map.get(month_name.lower()[:3], "01"))
    if is_valid_date(year_int, month_int, day_int):
        return f"{year_int}{month_int:02d}{day_int:02d}"
    return None


def _try_parse_date_match(
    match: tuple[str, ...],
    pattern: str,
    patterns: list[str],
    month_map: dict[str, str],
) -> str | None:
    """Try to parse a single regex match into a date.

    Args:
        match: Regex match tuple
        pattern: The pattern that matched
        patterns: Full list of patterns (for index comparison)
        month_map: Month name to number mapping

    Returns:
        Date string in YYYYMMDD format, or None if invalid
    """
    if len(match) != 3:
        return None

    try:
        if pattern == patterns[0]:  # MM/DD/YYYY or DD/MM/YYYY
            return _parse_ambiguous_date(match)
        elif pattern == patterns[1]:  # YYYY/MM/DD
            return _parse_iso_date(match)
        elif pattern == patterns[2]:  # DD Mon YYYY
            return _parse_day_month_year_date(match, month_map)
        elif pattern == patterns[3]:  # Mon DD, YYYY
            return _parse_month_day_year_date(match, month_map)
    except (ValueError, KeyError):
        pass
    return None


@lru_cache(maxsize=256)
def parse_date_from_text(
    text: str,
    date_patterns: tuple[str, ...] | None = None,
    month_map: tuple[tuple[str, str], ...] | None = None,
) -> str | None:
    """Parse date from text using various patterns.

    This function is cached for performance when processing similar text repeatedly.

    Args:
        text: Text to search for date patterns
        date_patterns: Tuple of regex patterns (defaults to DATE_PATTERNS)
        month_map: Tuple of (month_name, number) pairs (defaults to MONTH_MAP)

    Returns:
        Date string in YYYYMMDD format, or None if not found

    Examples:
        >>> parse_date_from_text("Report date: 15/03/2024")
        '20240315'
        >>> parse_date_from_text("Generated on 2024/03/15")
        '20240315'
    """
    patterns = list(date_patterns) if date_patterns else list(DATE_PATTERNS)
    months = dict(month_map) if month_map else dict(MONTH_MAP)

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Convert match to tuple if it's not already
            match_tuple = match if isinstance(match, tuple) else (match,)
            result = _try_parse_date_match(match_tuple, pattern, patterns, months)
            if result:
                return result
    return None


@lru_cache(maxsize=128)
def extract_date_from_study_id(study_id: str) -> str | None:
    """Extract date from study ID if it contains timestamp patterns.

    Looks for common timestamp patterns in study identifiers.

    Args:
        study_id: Study identifier string

    Returns:
        Date string in YYYYMMDD format, or None if not found

    Examples:
        >>> extract_date_from_study_id("study_20240315_001")
        '20240315'
        >>> extract_date_from_study_id("study-2024-03-15-a")
        '20240315'
    """
    # Look for timestamp patterns in study ID
    timestamp_patterns = [
        r"(\d{4})(\d{2})(\d{2})",  # YYYYMMDD
        r"(\d{4})-(\d{2})-(\d{2})",  # YYYY-MM-DD
        r"(\d{4})_(\d{2})_(\d{2})",  # YYYY_MM_DD
    ]

    for pattern in timestamp_patterns:
        match = re.search(pattern, study_id)
        if match:
            year, month, day = match.groups()
            try:
                year_int, month_int, day_int = int(year), int(month), int(day)
                # Validate date components using proper calendar validation
                if is_valid_date(year_int, month_int, day_int):
                    return f"{year_int}{month_int:02d}{day_int:02d}"
            except ValueError:
                continue

    return None


def get_fallback_date() -> str:
    """Get the default fallback date when no date can be extracted.

    Returns:
        Date string in YYYYMMDD format
    """
    return DEFAULT_FALLBACK_DATE
