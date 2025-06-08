"""
Wellbin Medical Data Downloader Core Module

Contains the main WellbinMedicalDownloader class for downloading medical data
from the Wellbin platform with support for FhirStudy and DicomStudy types.
"""

import os
import re
import time
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional

import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class WellbinMedicalDownloader:
    def __init__(
        self,
        email: str,
        password: str,
        headless: bool = True,
        limit_studies: Optional[int] = None,
        study_types: Optional[List[str]] = None,
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
        self.limit_studies = (
            limit_studies  # None = all studies, number = limit to that many
        )
        self.study_types = study_types or ["FhirStudy"]  # Default to FhirStudy only
        self.output_dir = output_dir
        self.study_dates: Dict[str, str] = {}  # Map study URLs to dates
        self.date_counters: DefaultDict[str, int] = defaultdict(
            int
        )  # For deduplication per study type

        # Study type configuration
        self.study_config: Dict[str, Dict[str, str]] = {
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

    def setup_driver(self) -> None:
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

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
            assert self.driver is not None, "Driver should be initialized"
            self.driver.get(self.login_url)
            time.sleep(2)

            # Fill login form
            print("📝 Filling login credentials...")
            email_field = self.driver.find_element(
                By.CSS_SELECTOR, "input[type='email']"
            )
            password_field = self.driver.find_element(
                By.CSS_SELECTOR, "input[type='password']"
            )

            email_field.clear()
            email_field.send_keys(self.email)
            password_field.clear()
            password_field.send_keys(self.password)

            # Submit form
            print("🚀 Submitting login form...")
            submit_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[type='submit']"
            )
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

        except Exception as e:
            print(f"❌ Error during login: {e}")
            return False

    def extract_study_dates_from_explorer(self) -> bool:
        """Extract study dates from the explorer page"""
        try:
            print("📅 Extracting study dates from explorer page...")
            assert self.driver is not None, "Driver should be initialized"
            self.driver.get(self.explorer_url)
            time.sleep(3)

            # Look for date patterns in the page
            # Common date patterns to look for
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

            # Find all study links and their associated dates
            study_elements = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, '/study/')]"
            )

            print(f"🔍 Found {len(study_elements)} study elements, extracting dates...")

            for element in study_elements:
                try:
                    href = element.get_attribute("href")
                    if not href or "study/" not in href:
                        continue

                    # Get the parent container to look for dates nearby
                    parent = element.find_element(
                        By.XPATH,
                        "./ancestor::*[contains(@class, 'study') or contains(@class, 'card') or contains(@class, 'item') or contains(@class, 'row')][1]",
                    )
                    container_text = parent.text if parent else element.text

                    # Also check siblings and nearby elements
                    try:
                        # Look for date in various nearby elements
                        nearby_elements = self.driver.find_elements(
                            By.XPATH,
                            f"//a[@href='{href}']/ancestor::*[1]//*[contains(text(), '202') or contains(text(), '201')]",
                        )
                        for nearby in nearby_elements:
                            container_text += " " + nearby.text
                    except:
                        pass

                    # Extract date from the container text
                    study_date = self.parse_date_from_text(
                        container_text, date_patterns, month_map
                    )

                    if study_date:
                        self.study_dates[href] = study_date
                        print(f"  📅 {href} -> {study_date}")
                    else:
                        # Fallback: extract from URL or use current date
                        study_id_match = re.search(r"/study/([^?]+)", href)
                        if study_id_match:
                            study_id = study_id_match.group(1)
                            # Try to extract date from study ID (some IDs contain timestamps)
                            fallback_date = self.extract_date_from_study_id(study_id)
                            if fallback_date:
                                self.study_dates[href] = fallback_date
                                print(f"  📅 {href} -> {fallback_date} (from ID)")
                            else:
                                # Use a default date pattern
                                self.study_dates[href] = "20240101"  # Default fallback
                                print(f"  ⚠️  {href} -> 20240101 (fallback)")

                except Exception as e:
                    print(f"  ❌ Error extracting date for element: {e}")
                    continue

            print(f"📊 Extracted dates for {len(self.study_dates)} studies")
            return True

        except Exception as e:
            print(f"❌ Error extracting study dates: {e}")
            return False

    def parse_date_from_text(
        self, text: str, date_patterns: List[str], month_map: Dict[str, str]
    ) -> Optional[str]:
        """Parse date from text using various patterns"""
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match) == 3:
                        if pattern == date_patterns[0]:  # MM/DD/YYYY or DD/MM/YYYY
                            # Handle both DD/MM/YYYY and MM/DD/YYYY formats
                            part1, part2, year = match
                            # Try to determine format based on values
                            if int(part1) > 12:  # Must be DD/MM/YYYY (day > 12)
                                day, month = part1, part2
                            elif int(part2) > 12:  # Must be MM/DD/YYYY (day > 12)
                                month, day = part1, part2
                            else:  # Ambiguous - assume DD/MM/YYYY (European format as shown in image)
                                day, month = part1, part2
                            return f"{year}{month.zfill(2)}{day.zfill(2)}"

                        elif pattern == date_patterns[1]:  # YYYY/MM/DD
                            year, month, day = match
                            return f"{year}{month.zfill(2)}{day.zfill(2)}"

                        elif pattern == date_patterns[2]:  # DD Mon YYYY
                            day, month_name, year = match
                            month = month_map.get(month_name, "01")
                            return f"{year}{month}{day.zfill(2)}"

                        elif pattern == date_patterns[3]:  # Mon DD, YYYY
                            month_name, day, year = match
                            month = month_map.get(month_name, "01")
                            return f"{year}{month}{day.zfill(2)}"

                except (ValueError, KeyError):
                    continue

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
                    # Validate date components
                    if (
                        1900 <= int(year) <= 2030
                        and 1 <= int(month) <= 12
                        and 1 <= int(day) <= 31
                    ):
                        return f"{year}{month.zfill(2)}{day.zfill(2)}"
                except ValueError:
                    continue

        return None

    def extract_dates_for_studies(self, study_links: List[str]) -> None:
        """Extract dates only for specific study links"""
        try:
            # Common date patterns to look for
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

            assert self.driver is not None, "Driver should be initialized"
            # Find study elements that match our filtered links
            for href in study_links:
                try:
                    # Find the specific study element by href
                    study_elements = self.driver.find_elements(
                        By.XPATH, f"//a[@href='{href}']"
                    )

                    for element in study_elements:
                        try:
                            # Get the parent container to look for dates nearby
                            parent = element.find_element(
                                By.XPATH,
                                "./ancestor::*[contains(@class, 'study') or contains(@class, 'card') or contains(@class, 'item') or contains(@class, 'row')][1]",
                            )
                            container_text = parent.text if parent else element.text

                            # Look for dates in the bottom area of study cards (like bottom-left in the image)
                            try:
                                # Look for date patterns in the entire parent container
                                date_elements = parent.find_elements(By.XPATH, ".//*")
                                for date_elem in date_elements:
                                    elem_text = date_elem.text.strip()
                                    if elem_text and (
                                        "/" in elem_text
                                        or any(char.isdigit() for char in elem_text)
                                    ):
                                        container_text += " " + elem_text

                                # Also check siblings and nearby elements
                                nearby_elements = self.driver.find_elements(
                                    By.XPATH,
                                    f"//a[@href='{href}']/ancestor::*[1]//*[contains(text(), '202') or contains(text(), '201') or contains(text(), '/')]",
                                )
                                for nearby in nearby_elements:
                                    if nearby.text.strip():
                                        container_text += " " + nearby.text
                            except:
                                pass

                            # Extract date from the container text
                            study_date = self.parse_date_from_text(
                                container_text, date_patterns, month_map
                            )

                            if study_date:
                                self.study_dates[href] = study_date
                                print(
                                    f"  📅 {href} -> {study_date} (found in text: '{container_text[:100]}...')"
                                )
                                break  # Found date for this study, move to next
                            else:
                                # Fallback: extract from URL or use current date
                                study_id_match = re.search(r"/study/([^?]+)", href)
                                if study_id_match:
                                    study_id = study_id_match.group(1)
                                    # Try to extract date from study ID (some IDs contain timestamps)
                                    fallback_date = self.extract_date_from_study_id(
                                        study_id
                                    )
                                    if fallback_date:
                                        self.study_dates[href] = fallback_date
                                        print(
                                            f"  📅 {href} -> {fallback_date} (from ID)"
                                        )
                                        break
                                    else:
                                        # Use a default date pattern
                                        self.study_dates[href] = (
                                            "20240101"  # Default fallback
                                        )
                                        print(f"  ⚠️  {href} -> 20240101 (fallback)")
                                        break

                        except Exception:
                            continue

                    # If no date found for this study, use fallback
                    if href not in self.study_dates:
                        self.study_dates[href] = "20240101"
                        print(f"  ⚠️  {href} -> 20240101 (no date found)")

                except Exception as e:
                    print(f"  ❌ Error extracting date for {href}: {e}")
                    self.study_dates[href] = "20240101"  # Fallback

            print(f"📊 Extracted dates for {len(self.study_dates)} studies")

        except Exception as e:
            print(f"❌ Error extracting study dates: {e}")

    def extract_date_from_study_page(self, study_url: str) -> str:
        """Extract date from the study page using the item-value report-date class"""
        try:
            assert self.driver is not None, "Driver should be initialized"
            # Look for the div with class "item-value report-date"
            date_element = self.driver.find_element(
                By.CSS_SELECTOR, "div.item-value.report-date"
            )
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

                parsed_date = self.parse_date_from_text(
                    date_text, date_patterns, month_map
                )
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

    def get_study_links(self) -> List[str]:
        """Get study links from the explorer page, filtered by study type"""
        try:
            print("🔍 Navigating to Explorer to find studies...")
            print(f"📍 Going to: {self.explorer_url}")
            assert self.driver is not None, "Driver should be initialized"
            self.driver.get(self.explorer_url)
            time.sleep(3)

            current_url = self.driver.current_url
            print(f"📍 Explorer page URL: {current_url}")

            # Look for study links
            study_links: List[str] = []

            # Find all links on the page
            print("🔎 Searching for study links...")
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            print(f"📊 Found {len(all_links)} total links on page")

            # Filter by study type FIRST
            print(f"🎯 Filtering for study types: {', '.join(self.study_types)}")

            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    if href and "study/" in href:
                        # Check if this study type is in our filter
                        study_type_found = False
                        for study_type in self.study_types:
                            if f"type={study_type}" in href:
                                study_type_found = True
                                study_links.append(href)
                                # Extract study type from URL for logging
                                print(f"  ✅ Found {study_type}: {href}")
                                break

                        # Handle "all" study types
                        if not study_type_found and "all" in self.study_types:
                            # Check if it's any of the known study types
                            if any(
                                f"type={st}" in href
                                for st in ["FhirStudy", "DicomStudy"]
                            ):
                                study_links.append(href)
                                print(f"  ✅ Found (all types): {href}")

                except Exception as e:
                    print(f"  ❌ Error processing link: {e}")
                    continue

            print(f"📊 Found {len(study_links)} matching study links")

            # Apply limit if specified
            if self.limit_studies and len(study_links) > self.limit_studies:
                print(
                    f"🔢 Limiting to {self.limit_studies} studies (found {len(study_links)})"
                )
                study_links = study_links[: self.limit_studies]

            # Note: Dates will be extracted when processing individual study pages
            # since they're not available on the explorer page

            return study_links

        except Exception as e:
            print(f"❌ Error getting study links: {e}")
            return []

    def get_pdf_from_study(
        self, study_url: str, study_index: int = 1, total_studies: int = 1
    ) -> List[Dict[str, Any]]:
        """Get PDF download links from a study page"""
        try:
            # Extract study type from URL
            type_match = re.search(r"type=([^&]+)", study_url)
            study_type = type_match.group(1) if type_match else "Unknown"

            print(
                f"\n[{study_index}/{total_studies}] 📄 Processing {study_type} study:"
            )
            print(f"  🔗 URL: {study_url}")

            assert self.driver is not None, "Driver should be initialized"
            self.driver.get(study_url)
            time.sleep(1)

            current_url = self.driver.current_url
            print(f"  📍 Loaded URL: {current_url}")

            # Extract the study date from the study page itself
            study_date = self.extract_date_from_study_page(study_url)
            print(f"  📅 Study date: {study_date}")

            # Look for the "Descargar estudio" button that points to S3
            print("  🔍 Looking for 'Descargar estudio' button...")

            try:
                # Go directly to S3 URL selector since we know it works
                elements = self.driver.find_elements(
                    By.XPATH, "//a[contains(@href, 'wellbin-uploads.s3')]"
                )

                download_element = None
                if elements:
                    # Take the first S3 link found
                    download_element = elements[0]
                    href = download_element.get_attribute("href")
                    text = download_element.text.strip()
                    print(
                        f"  ✅ Found S3 download link: '{text}' -> {href and href[:100]}..."
                    )

                if download_element:
                    href = download_element.get_attribute("href")
                    text = download_element.text.strip() or "Download"

                    pdf_info: Dict[str, Any] = {
                        "url": href,
                        "text": text,
                        "study_url": study_url,
                        "study_type": study_type,
                        "study_date": study_date,
                    }
                    print(f"  ✅ Found download link: {href and href[:100]}...")
                    return [pdf_info]
                else:
                    # Debug: show all links on the page
                    print("  🔍 All links on page:")
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")[
                        :10
                    ]  # First 10 links
                    for i, link in enumerate(all_links, 1):
                        href = link.get_attribute("href")
                        text = link.text.strip()
                        print(
                            f"    {i}. '{text}' -> {href[:80] if href else 'No href'}..."
                        )

                    print("  ❌ No S3 download link found")
                    return []

            except Exception as e:
                print(f"  ❌ Error finding download link: {e}")
                return []

        except Exception as e:
            print(f"  ❌ Error processing study {study_url}: {e}")
            return []

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
        pdf_info: Dict[str, Any],
        download_index: int = 1,
        total_downloads: int = 1,
    ) -> Optional[str]:
        """Download a PDF file"""
        try:
            study_date = pdf_info["study_date"]
            print(
                f"\n[{download_index}/{total_downloads}] 📥 Downloading {pdf_info['study_type']} PDF ({study_date}):"
            )
            print(f"  📝 Description: {pdf_info['text']}")
            print(f"  🔗 URL: {pdf_info['url'][:100]}...")

            # S3 URLs are pre-signed, no authentication needed
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

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
            config = self.study_config.get(
                pdf_info["study_type"], {"subdir": "unknown"}
            )
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
            print(f"  📏 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            return filepath

        except Exception as e:
            print(f"  ❌ Failed to download PDF: {e}")
            import traceback

            print(f"  🔍 Traceback: {traceback.format_exc()}")
            return None

    def scrape_studies(self) -> List[Dict[str, Any]]:
        """Main method to download studies and download PDFs"""
        downloaded_files: List[Dict[str, Any]] = []

        try:
            # Login
            if not self.login():
                print("❌ Login failed, cannot proceed")
                return downloaded_files

            # Get study links (this also extracts dates)
            study_links = self.get_study_links()
            if not study_links:
                print("❌ No study links found matching the filter")
                return downloaded_files

            print(f"\n🎯 Processing {len(study_links)} studies...")

            # Process each study
            all_pdf_links: List[Dict[str, Any]] = []
            for i, study_url in enumerate(study_links, 1):
                pdf_links = self.get_pdf_from_study(study_url, i, len(study_links))
                for pdf in pdf_links:
                    pdf["study_index"] = i
                all_pdf_links.extend(pdf_links)

                # Brief delay between studies
                if i < len(study_links):
                    time.sleep(0.5)

            if not all_pdf_links:
                print("❌ No PDF links found in any studies")
                return downloaded_files

            print(f"\n📊 Found {len(all_pdf_links)} total PDF files to download")
            print("=" * 60)

            # Download all PDFs
            for i, pdf_info in enumerate(all_pdf_links, 1):
                filepath = self.download_pdf(pdf_info, i, len(all_pdf_links))
                if filepath:
                    downloaded_files.append(
                        {
                            "local_path": filepath,
                            "original_url": pdf_info["url"],
                            "study_url": pdf_info["study_url"],
                            "study_type": pdf_info["study_type"],
                            "study_date": pdf_info["study_date"],
                            "description": pdf_info["text"],
                            "study_index": pdf_info["study_index"],
                        }
                    )

                # Brief delay between downloads
                if i < len(all_pdf_links):
                    time.sleep(0.2)

            return downloaded_files

        except Exception as e:
            print(f"❌ Error during download: {e}")
            import traceback

            print(f"🔍 Traceback: {traceback.format_exc()}")
            return downloaded_files
        finally:
            if self.driver:
                print("🔒 Closing browser...")
                self.driver.quit()
