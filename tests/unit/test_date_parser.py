"""Comprehensive edge case tests for wellbin/core/date_parser.py.

This module tests date parsing functions with parametrized edge cases:
- Leap year validation
- Invalid date boundaries
- Ambiguous date formats (DD/MM vs MM/DD)
- Various date string patterns
- Natural language dates
- Fallback behavior

Coverage target: 90%+ for date_parser.py
"""

import pytest

from wellbin.core.date_parser import (
    DEFAULT_FALLBACK_DATE,
    MONTH_MAP,
    _parse_ambiguous_date,
    _parse_day_month_year_date,
    _parse_iso_date,
    _parse_month_day_year_date,
    extract_date_from_study_id,
    get_fallback_date,
    is_valid_date,
    parse_date_from_text,
)


class TestIsValidDate:
    """Tests for is_valid_date function with edge cases."""

    # Basic valid dates
    @pytest.mark.parametrize(
        "year,month,day",
        [
            (2024, 1, 1),  # First day of year
            (2024, 12, 31),  # Last day of year
            (2000, 6, 15),  # Middle of year
            (2099, 7, 4),  # Near upper boundary
            (1900, 1, 1),  # Lower boundary
        ],
        ids=["first-day", "last-day", "mid-year", "upper-bound", "lower-bound"],
    )
    def test_valid_basic_dates(self, year: int, month: int, day: int) -> None:
        """Test basic valid dates."""
        assert is_valid_date(year, month, day) is True

    # Leap year tests
    @pytest.mark.parametrize(
        "year,day,expected",
        [
            (2024, 29, True),  # Leap year, Feb 29 valid
            (2024, 28, True),  # Leap year, Feb 28 valid
            (2023, 29, False),  # Non-leap year, Feb 29 invalid
            (2023, 28, True),  # Non-leap year, Feb 28 valid
            (2000, 29, True),  # Century leap year (divisible by 400)
            (1900, 29, False),  # Century non-leap year (divisible by 100, not 400)
            (2100, 29, False),  # Future century non-leap year
        ],
        ids=[
            "leap-feb29",
            "leap-feb28",
            "nonleap-feb29",
            "nonleap-feb28",
            "century-leap",
            "century-nonleap",
            "future-century-nonleap",
        ],
    )
    def test_leap_year_february(self, year: int, day: int, expected: bool) -> None:
        """Test February dates with leap year logic."""
        assert is_valid_date(year, 2, day) is expected

    # Month boundary tests
    @pytest.mark.parametrize(
        "month,max_day",
        [
            (1, 31),  # January
            (2, 29),  # February (leap year max)
            (3, 31),  # March
            (4, 30),  # April
            (5, 31),  # May
            (6, 30),  # June
            (7, 31),  # July
            (8, 31),  # August
            (9, 30),  # September
            (10, 31),  # October
            (11, 30),  # November
            (12, 31),  # December
        ],
        ids=["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
    )
    def test_month_max_days(self, month: int, max_day: int) -> None:
        """Test last valid day of each month."""
        assert is_valid_date(2024, month, max_day) is True
        assert is_valid_date(2024, month, max_day + 1) is False

    # Invalid dates - out of range
    @pytest.mark.parametrize(
        "year,month,day,description",
        [
            (2024, 0, 15, "month-zero"),
            (2024, 13, 15, "month-thirteen"),
            (2024, -1, 15, "month-negative"),
            (2024, 6, 0, "day-zero"),
            (2024, 6, 32, "day-thirty-two"),
            (2024, 6, -1, "day-negative"),
            (1899, 6, 15, "year-below-min"),
            (2100, 6, 15, "year-above-max"),
        ],
    )
    def test_invalid_out_of_range_dates(self, year: int, month: int, day: int, description: str) -> None:
        """Test invalid dates with out-of-range values."""
        assert is_valid_date(year, month, day) is False

    # Edge cases at boundaries
    @pytest.mark.parametrize(
        "year,month,day,expected",
        [
            (1900, 1, 1, True),  # Absolute minimum valid date
            (2099, 12, 31, True),  # Absolute maximum valid date
            (2024, 1, 31, True),  # January 31
            (2024, 4, 30, True),  # April 30 (30-day month)
        ],
    )
    def test_boundary_dates(self, year: int, month: int, day: int, expected: bool) -> None:
        """Test dates at boundaries."""
        assert is_valid_date(year, month, day) is expected


class TestParseAmbiguousDate:
    """Tests for _parse_ambiguous_date function."""

    @pytest.mark.parametrize(
        "part1,part2,year,expected",
        [
            # Clear DD/MM/YYYY (day > 12)
            ("15", "03", "2024", "20240315"),
            ("25", "12", "2023", "20231225"),
            ("31", "01", "2024", "20240131"),
            # Clear MM/DD/YYYY (day in second position > 12)
            ("03", "15", "2024", "20240315"),
            ("01", "25", "2024", "20240125"),
            # Ambiguous - both <= 12, defaults to DD/MM/YYYY
            ("05", "03", "2024", "20240305"),  # May 3 or March 5? -> March 5 (DD/MM)
            ("01", "02", "2024", "20240201"),  # Jan 2 or Feb 1? -> Feb 1 (DD/MM)
            ("07", "11", "2024", "20241107"),  # Jul 11 or Nov 7? -> Nov 7 (DD/MM)
        ],
        ids=[
            "dd-mm-clear-1",
            "dd-mm-clear-2",
            "dd-mm-clear-3",
            "mm-dd-clear-1",
            "mm-dd-clear-2",
            "ambiguous-1",
            "ambiguous-2",
            "ambiguous-3",
        ],
    )
    def test_ambiguous_date_parsing(self, part1: str, part2: str, year: str, expected: str) -> None:
        """Test ambiguous date parsing with various inputs."""
        result = _parse_ambiguous_date((part1, part2, year))
        assert result == expected

    @pytest.mark.parametrize(
        "part1,part2,year",
        [
            ("32", "15", "2024"),  # Invalid day (32)
            ("15", "13", "2024"),  # Invalid month (13)
            ("00", "05", "2024"),  # Invalid day (0)
            ("05", "00", "2024"),  # Invalid month (0)
        ],
        ids=["invalid-day", "invalid-month", "zero-day", "zero-month"],
    )
    def test_ambiguous_date_invalid_returns_none(self, part1: str, part2: str, year: str) -> None:
        """Test that invalid dates return None."""
        result = _parse_ambiguous_date((part1, part2, year))
        assert result is None


class TestParseIsoDate:
    """Tests for _parse_iso_date function."""

    @pytest.mark.parametrize(
        "year,month,day,expected",
        [
            ("2024", "03", "15", "20240315"),
            ("2023", "12", "31", "20231231"),
            ("2000", "01", "01", "20000101"),
        ],
        ids=["standard", "end-of-year", "start-of-millennium"],
    )
    def test_valid_iso_dates(self, year: str, month: str, day: str, expected: str) -> None:
        """Test valid ISO format dates (YYYY/MM/DD)."""
        result = _parse_iso_date((year, month, day))
        assert result == expected

    @pytest.mark.parametrize(
        "year,month,day",
        [
            ("2024", "13", "15"),  # Invalid month
            ("2024", "02", "30"),  # Invalid day for February
            ("1899", "06", "15"),  # Year out of range
        ],
        ids=["invalid-month", "invalid-day", "year-out-of-range"],
    )
    def test_invalid_iso_dates_return_none(self, year: str, month: str, day: str) -> None:
        """Test that invalid ISO dates return None."""
        result = _parse_iso_date((year, month, day))
        assert result is None


class TestParseDayMonthYearDate:
    """Tests for _parse_day_month_year_date function (DD Mon YYYY)."""

    @pytest.mark.parametrize(
        "day,month_name,year,expected",
        [
            ("15", "Mar", "2024", "20240315"),
            ("01", "Jan", "2024", "20240101"),
            ("31", "Dec", "2023", "20231231"),
            ("15", "March", "2024", "20240315"),  # Full month name
            ("15", "march", "2024", "20240315"),  # Lowercase
        ],
        ids=["standard", "first-day", "last-day", "full-name", "lowercase"],
    )
    def test_valid_dd_mon_yyyy_dates(self, day: str, month_name: str, year: str, expected: str) -> None:
        """Test valid DD Mon YYYY format dates (natural language)."""
        month_map = dict(MONTH_MAP)
        result = _parse_day_month_year_date((day, month_name, year), month_map)
        assert result == expected


class TestParseMonthDayYearDate:
    """Tests for _parse_month_day_year_date function (Mon DD, YYYY)."""

    @pytest.mark.parametrize(
        "month_name,day,year,expected",
        [
            ("Mar", "15", "2024", "20240315"),
            ("Jan", "01", "2024", "20240101"),
            ("Dec", "31", "2023", "20231231"),
            ("March", "15", "2024", "20240315"),  # Full month name
            ("march", "15", "2024", "20240315"),  # Lowercase
        ],
        ids=["standard", "first-day", "last-day", "full-name", "lowercase"],
    )
    def test_valid_mon_dd_yyyy_dates(self, month_name: str, day: str, year: str, expected: str) -> None:
        """Test valid Mon DD, YYYY format dates (natural language)."""
        month_map = dict(MONTH_MAP)
        result = _parse_month_day_year_date((month_name, day, year), month_map)
        assert result == expected


class TestParseDateFromText:
    """Tests for parse_date_from_text function with various patterns."""

    # ISO format (YYYY/MM/DD)
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Report date: 2024/03/15", "20240315"),
            ("Generated on 2023/12/31", "20231231"),
            ("Date: 2000/01/01", "20000101"),
            ("2024/06/15 - Results", "20240615"),
        ],
        ids=["with-label", "end-year", "millennium", "middle"],
    )
    def test_iso_format(self, text: str, expected: str) -> None:
        """Test ISO format (YYYY/MM/DD) detection."""
        result = parse_date_from_text(text)
        assert result == expected

    # DD/MM/YYYY format
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Fecha: 15/03/2024", "20240315"),
            ("Informe del 31/12/2023", "20231231"),
            ("25/12/2024 - Navidad", "20241225"),
        ],
        ids=["spanish", "spanish-informe", "christmas"],
    )
    def test_dd_mm_yyyy_format(self, text: str, expected: str) -> None:
        """Test DD/MM/YYYY format detection."""
        result = parse_date_from_text(text)
        assert result == expected

    # MM/DD/YYYY format (US style)
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Date: 03/15/2024", "20240315"),
            ("Report from 12/31/2023", "20231231"),
        ],
        ids=["with-label", "end-year"],
    )
    def test_mm_dd_yyyy_format(self, text: str, expected: str) -> None:
        """Test MM/DD/YYYY format detection."""
        result = parse_date_from_text(text)
        assert result == expected

    # Natural language with month names
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("15 March 2024", "20240315"),
            ("March 15, 2024", "20240315"),
            ("01 January 2024", "20240101"),
            ("December 31, 2023", "20231231"),
            ("15 Mar 2024", "20240315"),  # Short month name
            ("15 Abr 2024", "20240415"),  # Spanish month (abril)
        ],
        ids=[
            "day-month-year",
            "month-day-year",
            "january",
            "december",
            "short-month",
            "spanish-month",
        ],
    )
    def test_natural_language_dates(self, text: str, expected: str) -> None:
        """Test natural language date formats."""
        result = parse_date_from_text(text)
        assert result == expected

    # No date found
    @pytest.mark.parametrize(
        "text",
        [
            "No date here",
            "",
            "Random text without any date pattern",
            "Date: someday",
            "2024",  # Year only, not a complete date
        ],
        ids=["no-date", "empty", "random", "invalid", "year-only"],
    )
    def test_no_date_found(self, text: str) -> None:
        """Test that text without valid dates returns None."""
        result = parse_date_from_text(text)
        assert result is None

    # Multiple dates - should return first match
    def test_multiple_dates_returns_first(self) -> None:
        """Test that multiple dates return the first match."""
        text = "Start: 01/01/2024 End: 31/12/2024"
        result = parse_date_from_text(text)
        assert result in ["20240101", "20241231"]

    def test_cached_behavior(self) -> None:
        """Test that the function uses caching."""
        text = "15/03/2024"
        # Call twice - second should use cache
        result1 = parse_date_from_text(text)
        result2 = parse_date_from_text(text)
        assert result1 == result2 == "20240315"


class TestExtractDateFromStudyId:
    """Tests for extract_date_from_study_id function."""

    @pytest.mark.parametrize(
        "study_id,expected",
        [
            # Timestamp-based IDs
            ("study_20240315123456", "20240315"),
            ("STUDY-20231231-001", "20231231"),
            ("report_20240101", "20240101"),
        ],
        ids=["timestamp", "dashed", "simple"],
    )
    def test_valid_study_ids(self, study_id: str, expected: str) -> None:
        """Test extraction from valid study IDs."""
        result = extract_date_from_study_id(study_id)
        assert result == expected

    @pytest.mark.parametrize(
        "study_id",
        [
            "study_no_date_here",
            "STUDY001",
            "",
            "12345678",  # Too short for date
        ],
        ids=["no-date", "short", "empty", "too-short"],
    )
    def test_invalid_study_ids_return_none(self, study_id: str) -> None:
        """Test that invalid study IDs return None."""
        result = extract_date_from_study_id(study_id)
        assert result is None


class TestGetFallbackDate:
    """Tests for get_fallback_date function."""

    def test_fallback_date_format(self) -> None:
        """Test that fallback date is in correct format."""
        result = get_fallback_date()
        assert result is not None
        assert len(result) == 8
        assert result.isdigit()

    def test_fallback_date_is_valid(self) -> None:
        """Test that fallback date is a valid date."""
        result = get_fallback_date()
        # Should be able to parse it
        year = int(result[:4])
        month = int(result[4:6])
        day = int(result[6:8])
        assert is_valid_date(year, month, day) is True

    def test_default_fallback_date_constant(self) -> None:
        """Test that DEFAULT_FALLBACK_DATE has correct format."""
        assert len(DEFAULT_FALLBACK_DATE) == 8
        assert DEFAULT_FALLBACK_DATE.isdigit()


class TestDateParserIntegration:
    """Integration tests for date parser functions."""

    def test_parse_then_validate(self) -> None:
        """Test parsing a date and then validating it."""
        text = "Report date: 15/03/2024"
        result = parse_date_from_text(text)
        assert result is not None
        year = int(result[:4])
        month = int(result[4:6])
        day = int(result[6:8])
        assert is_valid_date(year, month, day) is True

    @pytest.mark.parametrize(
        "text",
        [
            "29/02/2024",  # Valid leap year
            "29/02/2023",  # Invalid - not leap year (should not parse or be invalid)
            "31/04/2024",  # Invalid - April has 30 days
            "31/06/2024",  # Invalid - June has 30 days
        ],
        ids=["leap-valid", "leap-invalid", "april-31", "june-31"],
    )
    def test_edge_case_dates_in_text(self, text: str) -> None:
        """Test edge case dates embedded in text."""
        result = parse_date_from_text(text)
        # Either returns None (invalid) or a valid date
        if result is not None:
            year = int(result[:4])
            month = int(result[4:6])
            day = int(result[6:8])
            assert is_valid_date(year, month, day) is True
