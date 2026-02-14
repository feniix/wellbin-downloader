"""
Wellbin Medical Data Downloader Core Module

Contains the main WellbinMedicalDownloader class for downloading medical data
from the Wellbin platform with support for FhirStudy and DicomStudy types.
"""

import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional

import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class PDFDownloadInfo:
    """Structured data for PDF download information."""

    url: str
    text: str
    study_url: str
    study_type: str
    study_date: str
    study_index: int = 0


@dataclass
class DownloadResult:
    """Result of a successful PDF download."""

    local_path: str
    original_url: str
    study_url: str
    study_type: str
    study_date: str
    description: str
    study_index: int = 0


class WellbinMedicalDownloader:
    def __init__(
        self,
        email: str,
        password: str,
        headless: bool = True,
        limit_studies: Optional[int] = None,
        study_types: Optional[list[str]] = None,
        output_dir: str = "downloads",
    ) -> None:
        self.email = email
        self.password = password
        self.base_url = "https://wellbin.co"
        self.login_url = "https://wellbin.co/login"
        self.explorer_url = "https://wellbin.co/explorer"
        self.session = requests.Session()
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait[webdriver.Chrome]] = None
        self.headless = headless
        self.limit_studies = limit_studies  # None = all studies, number = limit to that many
        self.study_types = study_types or ["FhirStudy"]  # Default to FhirStudy only
        self.output_dir = output_dir
        self.study_dates: dict[str, str] = {}  # Map study URLs to dates
        self.date_counters: defaultdict[str, int] = defaultdict(int)  # For deduplication per study type

        # Study type configuration
        self.study_config: dict[str, dict[str, str]] = {
            "FhirStudy": {
                "name": "lab",
                "description": "Laboratory Reports",
                "icon": "🧪",
                "subdir": "lab_reports",
            },
            "DicomStudy": {
                "name": "imaging",
                "description": "Medical Imaging",
                "icon": "🩻",
                "subdir": "imaging_reports",
            },
        }

    # Class constants for date handling
    DATE_PATTERNS: list[str] = [
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",  # MM/DD/YYYY or DD/MM/YYYY
        r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",  # YYYY/MM/DD
        r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b",  # DD Mon YYYY
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b",  # Mon DD, YYYY
    ]

    MONTH_MAP: dict[str, str] = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }

    DEFAULT_DATE: str = "20240101"
    KNOWN_STUDY_TYPES: tuple[str, ...] = ("FhirStudy", "DicomStudy")

    @staticmethod
    def _is_valid_date(year: int, month: int, day: int) -> bool:
        """Validate that date components form a valid calendar date."""
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

    @staticmethod
    def _sanitize_xpath_string(s: str) -> str:
        """Sanitize string for safe use in XPath expressions."""
        if "'" not in s:
            return f"'{s}'"
        if '"' not in s:
            return f'"{s}"'
        # For strings with both quotes, use concat() function
        parts = s.split("'")
        return "concat('" + "', \"'\", '".join(parts) + "')"

    def _matches_study_type(self, href: str, study_types: list[str]) -> bool:
        """Check if a URL matches any of the specified study types.

        Args:
            href: URL to check
            study_types: List of study types to match (e.g., ["FhirStudy"], ["all"])

        Returns:
            True if URL matches any study type filter
        """
        if "all" in study_types:
            # Check if it's any of the known study types
            return any(f"type={st}" in href for st in self.KNOWN_STUDY_TYPES)

        return any(f"type={study_type}" in href for study_type in study_types)

    def setup_driver(self) -> None:
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        chrome_options.add_argument(f"--user-agent={user_agent}")

        print("🔧 Setting up Chrome driver...")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)
        print("✅ Chrome driver ready")

    def login(self) -> bool:
        """Login to Wellbin"""
        try:
            print("🔐 Logging into Wellbin...")
            self.setup_driver()

            # Navigate to login page
            print(f"📍 Navigating to: {self.login_url}")
            assert self.driver is not None, "Driver should be initialized"  # nosec
            self.driver.get(self.login_url)
            time.sleep(2)

            # Fill login form
            print("📝 Filling login credentials...")
            email_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            email_field.clear()
            email_field.send_keys(self.email)
            password_field.clear()
            password_field.send_keys(self.password)

            # Submit form
            print("🚀 Submitting login form...")
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()

            time.sleep(3)

            # Verify login success
            current_url = self.driver.current_url
            print(f"📍 After login, current URL: {current_url}")

            if "dashboard" in current_url.lower():
                print("✅ Login successful!")
                return True
            else:
                print(f"❌ Login failed. Expected dashboard URL, got: {current_url}")
                return False

        except NoSuchElementException as e:
            print(f"❌ Login form element not found: {e}")
            print("   Check if login page structure has changed")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during login: {type(e).__name__}: {e}")
            import traceback

            print(traceback.format_exc())
            return False

    def extract_study_dates_from_explorer(self) -> bool:
        """Extract study dates from the explorer page."""
        try:
            print("📅 Extracting study dates from explorer page...")
            assert self.driver is not None, "Driver should be initialized"  # nosec
            self.driver.get(self.explorer_url)
            time.sleep(3)

            study_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/study/')]")
            print(f"🔍 Found {len(study_elements)} study elements, extracting dates...")

            for element in study_elements:
                self._extract_date_from_study_element(element)

            print(f"📊 Extracted dates for {len(self.study_dates)} studies")
            return True

        except Exception as e:
            print(f"❌ Error extracting study dates: {type(e).__name__}: {e}")
            import traceback

            print(f"Traceback: {traceback.format_exc()}")
            return False

    def _extract_date_from_study_element(self, element: Any) -> None:
        """Extract date from a single study element.

        Args:
            element: Selenium WebElement for the study link
        """
        try:
            href = element.get_attribute("href")
            if not href or "study/" not in href:
                return

            container_text = self._get_study_container_text(element, href)

            # Try to parse date from container text
            study_date = self.parse_date_from_text(container_text)

            if not study_date:
                # Fallback to ID extraction or default
                study_date = self._get_fallback_date(href)

            self.study_dates[href] = study_date
            self._log_date_extraction(href, study_date)

        except Exception as e:
            print(f"  ❌ Error extracting date for element: {type(e).__name__}: {e}")

    def _get_study_container_text(self, element: Any, href: str) -> str:
        """Get container text for a study element.

        Args:
            element: Selenium WebElement
            href: Study URL

        Returns:
            Combined text from container and nearby elements
        """
        try:
            parent_xpath = (
                "./ancestor::*[contains(@class, 'study') or "
                "contains(@class, 'card') or "
                "contains(@class, 'item') or "
                "contains(@class, 'row')][1]"
            )
            parent = element.find_element(By.XPATH, parent_xpath)
            container_text = parent.text if parent else element.text

            # Add nearby date text
            href_xpath = self._sanitize_xpath_string(href)
            container_text += self._collect_nearby_date_text(href_xpath)

            return container_text

        except Exception as e:  # noqa: S110
            print(f"    ⚠️  Could not extract nearby date elements: {type(e).__name__}")
            return element.text if element else ""

    def parse_date_from_text(
        self,
        text: str,
        date_patterns: Optional[list[str]] = None,
        month_map: Optional[dict[str, str]] = None,
    ) -> Optional[str]:
        """Parse date from text using various patterns.

        Args:
            text: Text to search for date patterns
            date_patterns: List of regex patterns (defaults to class constants)
            month_map: Month name to number mapping (defaults to class constants)

        Returns:
            Date string in YYYYMMDD format, or None if not found
        """
        patterns = date_patterns or self.DATE_PATTERNS
        months = month_map or self.MONTH_MAP

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                result = self._try_parse_date_match(match, pattern, patterns, months)
                if result:
                    return result
        return None

    def _try_parse_date_match(
        self,
        match: tuple[str, ...],
        pattern: str,
        patterns: list[str],
        month_map: dict[str, str],
    ) -> Optional[str]:
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
                return self._parse_ambiguous_date(match)
            elif pattern == patterns[1]:  # YYYY/MM/DD
                return self._parse_iso_date(match)
            elif pattern == patterns[2]:  # DD Mon YYYY
                return self._parse_day_month_year_date(match, month_map)
            elif pattern == patterns[3]:  # Mon DD, YYYY
                return self._parse_month_day_year_date(match, month_map)
        except (ValueError, KeyError):
            pass
        return None

    def _parse_ambiguous_date(self, match: tuple[str, ...]) -> Optional[str]:
        """Parse ambiguous DD/MM vs MM/DD format."""
        part1, part2, year = match
        part1_int, part2_int, year_int = int(part1), int(part2), int(year)

        # Try to determine format based on values
        if part1_int > 12:  # Must be DD/MM/YYYY (day > 12)
            day, month = part1_int, part2_int
        elif part2_int > 12:  # Must be MM/DD/YYYY (day > 12)
            month, day = part1_int, part2_int
        else:  # Ambiguous - assume DD/MM/YYYY (European format)
            day, month = part1_int, part2_int

        if self._is_valid_date(year_int, month, day):
            return f"{year_int}{month:02d}{day:02d}"
        return None

    def _parse_iso_date(self, match: tuple[str, ...]) -> Optional[str]:
        """Parse YYYY/MM/DD format."""
        year_str, month_str, day_str = match
        year_int, month_int, day_int = int(year_str), int(month_str), int(day_str)
        if self._is_valid_date(year_int, month_int, day_int):
            return f"{year_int}{month_int:02d}{day_int:02d}"
        return None

    def _parse_day_month_year_date(self, match: tuple[str, ...], month_map: dict[str, str]) -> Optional[str]:
        """Parse DD Mon YYYY format."""
        day_str, month_name, year_str = match
        day_int, year_int = int(day_str), int(year_str)
        month_int = int(month_map.get(month_name, "01"))
        if self._is_valid_date(year_int, month_int, day_int):
            return f"{year_int}{month_int:02d}{day_int:02d}"
        return None

    def _parse_month_day_year_date(self, match: tuple[str, ...], month_map: dict[str, str]) -> Optional[str]:
        """Parse Mon DD, YYYY format."""
        month_name, day_str, year_str = match
        day_int, year_int = int(day_str), int(year_str)
        month_int = int(month_map.get(month_name, "01"))
        if self._is_valid_date(year_int, month_int, day_int):
            return f"{year_int}{month_int:02d}{day_int:02d}"
        return None

    def extract_date_from_study_id(self, study_id: str) -> Optional[str]:
        """Extract date from study ID if it contains timestamp patterns"""
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
                    if self._is_valid_date(year_int, month_int, day_int):
                        return f"{year_int}{month_int:02d}{day_int:02d}"
                except ValueError:
                    continue

        return None

    def extract_dates_for_studies(self, study_links: list[str]) -> None:
        """Extract dates only for specific study links."""
        try:
            assert self.driver is not None, "Driver should be initialized"  # nosec

            for href in study_links:
                date = self._extract_date_for_single_study(href)
                self.study_dates[href] = date
                self._log_date_extraction(href, date)

            print(f"📊 Extracted dates for {len(self.study_dates)} studies")

        except Exception as e:
            print(f"❌ Error extracting study dates: {e}")

    def _extract_date_for_single_study(self, href: str) -> str:
        """Extract date for a single study URL.

        Args:
            href: Study URL to extract date from

        Returns:
            Date string in YYYYMMDD format
        """
        try:
            assert self.driver is not None, "Driver should be initialized"  # nosec
            href_xpath = self._sanitize_xpath_string(href)
            study_elements = self.driver.find_elements(By.XPATH, f"//a[@href={href_xpath}]")

            for element in study_elements:
                container_text = self._extract_container_text(element, href_xpath)
                study_date = self.parse_date_from_text(container_text)

                if study_date:
                    return study_date

            # Try fallback extraction
            return self._get_fallback_date(href)

        except Exception as e:
            print(f"  ❌ Error extracting date for {href}: {e}")
            return self.DEFAULT_DATE

    def _extract_container_text(self, element: Any, href_xpath: str) -> str:
        """Extract all relevant text from an element's container.

        Args:
            element: Selenium WebElement
            href_xpath: Sanitized XPath for the href

        Returns:
            Combined text from container and nearby elements
        """
        try:
            parent_xpath = (
                "./ancestor::*[contains(@class, 'study') or "
                "contains(@class, 'card') or "
                "contains(@class, 'item') or "
                "contains(@class, 'row')][1]"
            )
            parent = element.find_element(By.XPATH, parent_xpath)
            container_text = parent.text if parent else element.text

            # Add text from child elements that might contain dates
            container_text += self._collect_date_like_text(parent)
            container_text += self._collect_nearby_date_text(href_xpath)

            return container_text

        except Exception as e:
            print(f"    ⚠️  Could not extract container text: {type(e).__name__}")
            return element.text if element else ""

    def _collect_date_like_text(self, parent: Any) -> str:
        """Collect text from child elements that look like dates.

        Args:
            parent: Parent Selenium WebElement

        Returns:
            Combined text that might contain date information
        """
        additional_text = ""
        try:
            date_elements = parent.find_elements(By.XPATH, ".//*")
            for date_elem in date_elements:
                elem_text = date_elem.text.strip()
                if elem_text and self._looks_like_date_text(elem_text):
                    additional_text += " " + elem_text
        except Exception as e:  # noqa: S110
            print(f"    ⚠️  Could not extract date patterns from parent: {type(e).__name__}")
        return additional_text

    def _collect_nearby_date_text(self, href_xpath: str) -> str:
        """Collect text from nearby elements that might contain dates.

        Args:
            href_xpath: Sanitized XPath for the href

        Returns:
            Combined text from nearby elements
        """
        additional_text = ""
        try:
            nearby_xpath = (
                f"//a[@href={href_xpath}]/ancestor::*[1]//*["
                "contains(text(), '202') or "
                "contains(text(), '201') or "
                "contains(text(), '/')]"
            )
            assert self.driver is not None, "Driver should be initialized"  # nosec
            nearby_elements = self.driver.find_elements(By.XPATH, nearby_xpath)
            for nearby in nearby_elements:
                if nearby.text.strip():
                    additional_text += " " + nearby.text
        except Exception:  # noqa: S110
            pass
        return additional_text

    @staticmethod
    def _looks_like_date_text(text: str) -> bool:
        """Check if text looks like it might contain a date.

        Args:
            text: Text to check

        Returns:
            True if text might contain date information
        """
        return "/" in text or any(char.isdigit() for char in text)

    def _get_fallback_date(self, href: str) -> str:
        """Get a fallback date from URL or use default.

        Args:
            href: Study URL to extract date from

        Returns:
            Date string in YYYYMMDD format
        """
        study_id_match = re.search(r"/study/([^?]+)", href)
        if study_id_match:
            study_id = study_id_match.group(1)
            fallback_date = self.extract_date_from_study_id(study_id)
            if fallback_date:
                return fallback_date

        return self.DEFAULT_DATE

    def _log_date_extraction(self, href: str, date: str) -> None:
        """Log the result of date extraction.

        Args:
            href: Study URL
            date: Extracted date string
        """
        if date == self.DEFAULT_DATE:
            print(f"  ⚠️  {href} -> {date} (fallback)")
        else:
            print(f"  📅 {href} -> {date}")

    def extract_date_from_study_page(self, study_url: str) -> str:
        """Extract date from the study page using the item-value report-date class"""
        try:
            assert self.driver is not None, "Driver should be initialized"  # nosec
            # Look for the div with class "item-value report-date"
            date_element = self.driver.find_element(By.CSS_SELECTOR, "div.item-value.report-date")
            date_text = date_element.text.strip()

            if date_text:
                print(f"    🔍 Found date text: '{date_text}'")

                # Parse the date using our existing parsing logic
                date_patterns = [
                    r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",  # MM/DD/YYYY or DD/MM/YYYY
                    r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",  # YYYY/MM/DD
                    r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b",  # DD Mon YYYY
                    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b",  # Mon DD, YYYY
                ]

                month_map = {
                    "Jan": "01",
                    "Feb": "02",
                    "Mar": "03",
                    "Apr": "04",
                    "May": "05",
                    "Jun": "06",
                    "Jul": "07",
                    "Aug": "08",
                    "Sep": "09",
                    "Oct": "10",
                    "Nov": "11",
                    "Dec": "12",
                }

                parsed_date = self.parse_date_from_text(date_text, date_patterns, month_map)
                if parsed_date:
                    return parsed_date

            # Fallback to study ID extraction if date parsing fails
            study_id_match = re.search(r"/study/([^?]+)", study_url)
            if study_id_match:
                study_id = study_id_match.group(1)
                fallback_date = self.extract_date_from_study_id(study_id)
                if fallback_date:
                    print(f"    ⚠️  Using fallback date from ID: {fallback_date}")
                    return fallback_date

            print("    ⚠️  No date found, using default")
            return "20240101"  # Default fallback

        except NoSuchElementException:
            print("    ❌ Could not find div.item-value.report-date element")
            return "20240101"  # Default fallback
        except Exception as e:
            print(f"    ❌ Error extracting date from study page: {e}")
            return "20240101"  # Default fallback

    def get_study_links(self) -> list[str]:
        """Get study links from the explorer page, filtered by study type."""
        try:
            self._navigate_to_explorer()

            study_links = self._collect_study_links()

            return self._apply_study_limit(study_links)

        except Exception as e:
            print(f"❌ Error getting study links: {e}")
            return []

    def _navigate_to_explorer(self) -> None:
        """Navigate to the explorer page."""
        print("🔍 Navigating to Explorer to find studies...")
        print(f"📍 Going to: {self.explorer_url}")
        assert self.driver is not None, "Driver should be initialized"  # nosec
        self.driver.get(self.explorer_url)
        time.sleep(3)
        print(f"📍 Explorer page URL: {self.driver.current_url}")

    def _collect_study_links(self) -> list[str]:
        """Collect and filter study links from the current page."""
        print("🔎 Searching for study links...")
        assert self.driver is not None, "Driver should be initialized"  # nosec
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        print(f"📊 Found {len(all_links)} total links on page")

        print(f"🎯 Filtering for study types: {', '.join(self.study_types)}")

        study_links: list[str] = []
        for link in all_links:
            href = self._extract_valid_study_link(link)
            if href and self._matches_study_type(href, self.study_types):
                study_links.append(href)
                print(f"  ✅ Found: {href}")

        print(f"📊 Found {len(study_links)} matching study links")
        return study_links

    def _extract_valid_study_link(self, link: Any) -> Optional[str]:
        """Extract href from a link element if it's a valid study link."""
        try:
            href = link.get_attribute("href")
            if href and "study/" in href:
                return href
        except Exception as e:
            print(f"  ❌ Error processing link: {e}")
        return None

    def _apply_study_limit(self, study_links: list[str]) -> list[str]:
        """Apply study limit if configured."""
        if self.limit_studies and len(study_links) > self.limit_studies:
            print(f"🔢 Limiting to {self.limit_studies} studies (found {len(study_links)})")
            return study_links[: self.limit_studies]
        return study_links

    def get_pdf_from_study(self, study_url: str, study_index: int = 1, total_studies: int = 1) -> list[dict[str, Any]]:
        """Get PDF download links from a study page.

        Args:
            study_url: URL of the study page
            study_index: Current study index (for progress display)
            total_studies: Total number of studies (for progress display)

        Returns:
            List of PDF download info dictionaries
        """
        try:
            study_type = self._extract_study_type(study_url)
            self._print_study_progress(study_url, study_index, total_studies, study_type)

            self._navigate_to_study(study_url)
            study_date = self._extract_study_date(study_url)

            return self._find_pdf_download_links(study_url, study_type, study_date)

        except Exception as e:
            print(f"  ❌ Error processing study {study_url}: {e}")
            return []

    def _extract_study_type(self, study_url: str) -> str:
        """Extract study type from URL.

        Args:
            study_url: Study page URL

        Returns:
            Study type string (e.g., "FhirStudy", "DicomStudy")
        """
        type_match = re.search(r"type=([^&]+)", study_url)
        return type_match.group(1) if type_match else "Unknown"

    def _print_study_progress(self, study_url: str, index: int, total: int, study_type: str) -> None:
        """Print study processing progress.

        Args:
            study_url: Study page URL
            index: Current study index
            total: Total number of studies
            study_type: Type of study
        """
        print(f"\n[{index}/{total}] 📄 Processing {study_type} study:")
        print(f"  🔗 URL: {study_url}")

    def _navigate_to_study(self, study_url: str) -> None:
        """Navigate to study page.

        Args:
            study_url: URL to navigate to
        """
        assert self.driver is not None, "Driver should be initialized"  # nosec
        self.driver.get(study_url)
        time.sleep(1)
        print(f"  📍 Loaded URL: {self.driver.current_url}")

    def _extract_study_date(self, study_url: str) -> str:
        """Extract and print study date.

        Args:
            study_url: Study page URL

        Returns:
            Study date string
        """
        study_date = self.extract_date_from_study_page(study_url)
        print(f"  📅 Study date: {study_date}")
        return study_date

    def _find_pdf_download_links(self, study_url: str, study_type: str, study_date: str) -> list[dict[str, Any]]:
        """Find PDF download links on study page.

        Args:
            study_url: Study page URL
            study_type: Type of study
            study_date: Study date string

        Returns:
            List of PDF download info dictionaries
        """
        print("  🔍 Looking for 'Descargar estudio' button...")

        try:
            elements = self._find_s3_download_elements()

            if elements:
                return self._process_download_element(elements[0], study_url, study_type, study_date)

            self._print_available_links()
            print("  ❌ No S3 download link found")
            return []

        except Exception as e:
            print(f"  ❌ Error finding download link: {e}")
            return []

    def _find_s3_download_elements(self) -> list[Any]:
        """Find S3 download link elements on page.

        Returns:
            List of Selenium WebElement objects
        """
        assert self.driver is not None, "Driver should be initialized"  # nosec
        elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'wellbin-uploads.s3')]")

        if elements:
            href = elements[0].get_attribute("href")
            text = elements[0].text.strip()
            print(f"  ✅ Found S3 download link: '{text}' -> {href and href[:100]}...")

        return elements

    def _process_download_element(
        self, element: Any, study_url: str, study_type: str, study_date: str
    ) -> list[dict[str, Any]]:
        """Process a download element and return PDF info.

        Args:
            element: Selenium WebElement for download link
            study_url: Study page URL
            study_type: Type of study
            study_date: Study date string

        Returns:
            List containing single PDF info dictionary
        """
        href = element.get_attribute("href")
        text = element.text.strip() or "Download"

        print(f"  ✅ Found download link: {href and href[:100]}...")

        return [
            {
                "url": href,
                "text": text,
                "study_url": study_url,
                "study_type": study_type,
                "study_date": study_date,
            }
        ]

    def _print_available_links(self) -> None:
        """Print available links on page for debugging."""
        print("  🔍 All links on page:")
        assert self.driver is not None, "Driver should be initialized"  # nosec
        all_links = self.driver.find_elements(By.TAG_NAME, "a")[:10]

        for i, link in enumerate(all_links, 1):
            href = link.get_attribute("href")
            text = link.text.strip()
            print(f"    {i}. '{text}' -> {href[:80] if href else 'No href'}...")

    def _extract_study_type_from_url(self, url: str) -> str:
        """Extract study type from URL parameter.

        Args:
            url: Study URL containing type parameter

        Returns:
            Study type string or "Unknown"
        """
        type_match = re.search(r"type=([^&]+)", url)
        return type_match.group(1) if type_match else "Unknown"

    def _print_study_header(self, study_type: str, study_url: str, index: int, total: int) -> None:
        """Print study processing header.

        Args:
            study_type: Type of study being processed
            study_url: URL of the study
            index: Current study index
            total: Total number of studies
        """
        print(f"\n[{index}/{total}] 📄 Processing {study_type} study:")
        print(f"  🔗 URL: {study_url}")

    def generate_filename(self, study_date: str, study_type: str) -> str:
        """Generate filename with deduplication using format YYYYMMDD-{type}-N.pdf"""
        if study_date == "unknown":
            study_date = "20240101"  # Fallback

        # Get study type configuration
        config = self.study_config.get(study_type, {"name": "unknown"})
        type_name = config["name"]

        # Use study type + date as key for deduplication
        dedup_key = f"{study_type}_{study_date}"
        counter = self.date_counters[dedup_key]
        self.date_counters[dedup_key] += 1

        # Generate filename with counter (0-9)
        filename = f"{study_date}-{type_name}-{counter}.pdf"

        return filename

    def download_pdf(
        self,
        pdf_info: dict[str, Any],
        download_index: int = 1,
        total_downloads: int = 1,
    ) -> Optional[str]:
        """Download a PDF file"""
        try:
            study_date = pdf_info["study_date"]
            print(f"\n[{download_index}/{total_downloads}] 📥 Downloading {pdf_info['study_type']} PDF ({study_date}):")
            print(f"  📝 Description: {pdf_info['text']}")
            print(f"  🔗 URL: {pdf_info['url'][:100]}...")

            # S3 URLs are pre-signed, no authentication needed
            user_agent = (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
            headers = {"User-Agent": user_agent}

            print("  🌐 Making download request...")
            response = self.session.get(pdf_info["url"], headers=headers, stream=True)
            print(f"  📊 Response status: {response.status_code}")

            if response.status_code != 200:
                print(f"  ❌ Bad response status: {response.status_code}")
                return None

            response.raise_for_status()

            # Generate filename based on study date and type
            filename = self.generate_filename(study_date, pdf_info["study_type"])
            print(f"  📁 Generated filename: {filename}")

            # Create output directories
            config = self.study_config.get(pdf_info["study_type"], {"subdir": "unknown"})
            output_subdir = os.path.join(self.output_dir, config["subdir"])
            os.makedirs(output_subdir, exist_ok=True)
            filepath = os.path.join(output_subdir, filename)

            # Download file
            print(f"  💾 Saving to: {filepath}")
            file_size = 0
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        file_size += len(chunk)

            print("  ✅ Downloaded successfully!")
            print(f"  📏 File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            return filepath

        except Exception as e:
            print(f"  ❌ Failed to download PDF: {e}")
            import traceback

            print(f"  🔍 Traceback: {traceback.format_exc()}")
            return None

    def scrape_studies(self) -> list[dict[str, Any]]:
        """Main method to download studies and download PDFs."""
        downloaded_files: list[dict[str, Any]] = []

        try:
            if not self._ensure_login():
                return downloaded_files

            study_links = self.get_study_links()
            if not study_links:
                print("❌ No study links found matching the filter")
                return downloaded_files

            print(f"\n🎯 Processing {len(study_links)} studies...")

            all_pdf_links = self._collect_all_pdf_links(study_links)
            if not all_pdf_links:
                print("❌ No PDF links found in any studies")
                return downloaded_files

            print(f"\n📊 Found {len(all_pdf_links)} total PDF files to download")
            print("=" * 60)

            downloaded_files = self._download_all_pdfs(all_pdf_links)
            return downloaded_files

        except Exception as e:
            print(f"❌ Error during download: {type(e).__name__}: {e}")
            import traceback

            print(f"🔍 Traceback: {traceback.format_exc()}")
            return downloaded_files
        finally:
            self._cleanup_resources()

    def _ensure_login(self) -> bool:
        """Ensure successful login.

        Returns:
            True if login successful, False otherwise
        """
        if not self.login():
            print("❌ Login failed, cannot proceed")
            return False
        return True

    def _collect_all_pdf_links(self, study_links: list[str]) -> list[PDFDownloadInfo]:
        """Collect PDF download links from all studies.

        Args:
            study_links: List of study URLs to process

        Returns:
            List of PDFDownloadInfo objects
        """
        all_pdf_links: list[PDFDownloadInfo] = []
        total_studies = len(study_links)

        for i, study_url in enumerate(study_links, 1):
            pdf_links = self.get_pdf_from_study(study_url, i, total_studies)
            for pdf in pdf_links:
                pdf["study_index"] = i
                all_pdf_links.append(PDFDownloadInfo(**pdf))

            if i < total_studies:
                time.sleep(0.5)

        return all_pdf_links

    def _download_all_pdfs(self, pdf_links: list[PDFDownloadInfo]) -> list[dict[str, Any]]:
        """Download all PDFs and return results.

        Args:
            pdf_links: List of PDF download information

        Returns:
            List of download result dictionaries
        """
        downloaded_files: list[dict[str, Any]] = []
        total_pdfs = len(pdf_links)

        for i, pdf_info in enumerate(pdf_links, 1):
            filepath = self.download_pdf(pdf_info.__dict__, i, total_pdfs)
            if filepath:
                result = DownloadResult(
                    local_path=filepath,
                    original_url=pdf_info.url,
                    study_url=pdf_info.study_url,
                    study_type=pdf_info.study_type,
                    study_date=pdf_info.study_date,
                    description=pdf_info.text,
                    study_index=pdf_info.study_index,
                )
                downloaded_files.append(result.__dict__)

            if i < total_pdfs:
                time.sleep(0.2)

        return downloaded_files

    def _cleanup_resources(self) -> None:
        """Clean up browser and session resources."""
        try:
            if self.driver:
                print("🔒 Closing browser...")
                self.driver.quit()
        except Exception as e:
            print(f"⚠️  Error closing browser: {type(e).__name__}: {e}")

        try:
            if self.session:
                self.session.close()
        except Exception as e:
            print(f"⚠️  Error closing session: {type(e).__name__}: {e}")
