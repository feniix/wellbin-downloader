#!/usr/bin/env python3
"""
Wellbin Medical Data Scraper
Universal scraper for downloading medical data from Wellbin platform
Supports FhirStudy (lab reports) and DicomStudy (imaging reports) with proper categorization
"""

import os
import re
import time
from collections import defaultdict
from datetime import datetime

import click
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Load environment variables
load_dotenv()


class WellbinMedicalScraper:
    def __init__(
        self,
        email,
        password,
        headless=True,
        limit_studies=None,
        study_types=None,
        output_dir="downloads",
    ):
        self.email = email
        self.password = password
        self.base_url = "https://wellbin.co"
        self.login_url = "https://wellbin.co/login"
        self.explorer_url = "https://wellbin.co/explorer"
        self.session = requests.Session()
        self.driver = None
        self.wait = None
        self.headless = headless
        self.limit_studies = (
            limit_studies  # None = all studies, number = limit to that many
        )
        self.study_types = study_types or ["FhirStudy"]  # Default to FhirStudy only
        self.output_dir = output_dir
        self.study_dates = {}  # Map study URLs to dates
        self.date_counters = defaultdict(int)  # For deduplication per study type

        # Study type configuration
        self.study_config = {
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

    def setup_driver(self):
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

    def login(self):
        """Login to Wellbin"""
        try:
            print("🔐 Logging into Wellbin...")
            self.setup_driver()

            # Navigate to login page
            print(f"📍 Navigating to: {self.login_url}")
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

    def extract_study_dates_from_explorer(self):
        """Extract study dates from the explorer page"""
        try:
            print("📅 Extracting study dates from explorer page...")
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

    def parse_date_from_text(self, text, date_patterns, month_map):
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

    def extract_date_from_study_id(self, study_id):
        """Try to extract date from study ID if it contains timestamp-like data"""
        try:
            # Some study IDs might contain hex timestamps or other date indicators
            # Try to find year patterns in the ID
            year_matches = re.findall(r"(20\d{2})", study_id)
            if year_matches:
                year = year_matches[0]
                return f"{year}0101"  # Use January 1st of that year

            # If the ID looks like a hex timestamp, try to decode it
            if len(study_id) >= 8:
                try:
                    # Try to interpret first 8 chars as hex timestamp
                    timestamp = int(study_id[:8], 16)
                    if timestamp > 1000000000:  # Reasonable timestamp range
                        date_obj = datetime.fromtimestamp(timestamp)
                        return date_obj.strftime("%Y%m%d")
                except:
                    pass

            return None
        except:
            return None

    def extract_dates_for_studies(self, study_links):
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

    def extract_date_from_study_page(self, study_url):
        """Extract date from the study page using the item-value report-date class"""
        try:
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

    def get_study_links(self):
        """Get study links from the explorer page, filtered by study type"""
        try:
            print("🔍 Navigating to Explorer to find studies...")
            print(f"📍 Going to: {self.explorer_url}")
            self.driver.get(self.explorer_url)
            time.sleep(3)

            current_url = self.driver.current_url
            print(f"📍 Explorer page URL: {current_url}")

            # Look for study links
            study_links = []

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
                                type_match = re.search(r"type=([^&]+)", href)
                                study_type = (
                                    type_match.group(1) if type_match else "Unknown"
                                )
                                print(f"  🔗 Found {study_type}: {href}")
                                break

                        # If 'all' is specified, include all study types
                        if "all" in self.study_types and not study_type_found:
                            study_links.append(href)
                            # Extract study type from URL for logging
                            type_match = re.search(r"type=([^&]+)", href)
                            study_type = (
                                type_match.group(1) if type_match else "Unknown"
                            )
                            print(f"  🔗 Found {study_type}: {href}")

                except:
                    continue

            # Remove duplicates while preserving order
            unique_study_links = []
            seen = set()
            for link in study_links:
                if link not in seen:
                    unique_study_links.append(link)
                    seen.add(link)

            print(
                f"📚 Found {len(unique_study_links)} unique study links matching filter"
            )

            # Apply limit if specified
            if self.limit_studies and self.limit_studies > 0:
                unique_study_links = unique_study_links[: self.limit_studies]
                print(f"🔢 Limited to first {len(unique_study_links)} studies")

            # Dates will be extracted from individual study pages during processing

            return unique_study_links

        except Exception as e:
            print(f"❌ Error getting study links: {e}")
            return []

    def get_pdf_from_study(self, study_url, study_index=1, total_studies=1):
        """Get PDF download link from a specific study page"""
        try:
            # Extract study type from URL for display
            type_match = re.search(r"type=([^&]+)", study_url)
            study_type = type_match.group(1) if type_match else "Unknown"

            print(
                f"\n[{study_index}/{total_studies}] 📄 Processing {study_type} study:"
            )
            print(f"  🔗 URL: {study_url}")

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
                    print(f"  ✅ Found S3 download link: '{text}' -> {href[:100]}...")

                if download_element:
                    href = download_element.get_attribute("href")
                    text = download_element.text.strip() or "Download"

                    pdf_info = {
                        "url": href,
                        "text": text,
                        "study_url": study_url,
                        "study_type": study_type,
                        "study_date": study_date,
                    }
                    print(f"  ✅ Found download link: {href[:100]}...")
                    return [pdf_info]
                else:
                    # Debug: show all links on the page
                    print(f"  🔍 All links on page:")
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")[
                        :10
                    ]  # First 10 links
                    for i, link in enumerate(all_links, 1):
                        href = link.get_attribute("href")
                        text = link.text.strip()
                        print(
                            f"    {i}. '{text}' -> {href[:80] if href else 'No href'}..."
                        )

                    print(f"  ❌ No S3 download link found")
                    return []

            except Exception as e:
                print(f"  ❌ Error finding download link: {e}")
                return []

        except Exception as e:
            print(f"  ❌ Error processing study {study_url}: {e}")
            return []

    def generate_filename(self, study_date, study_type):
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

    def download_pdf(self, pdf_info, download_index=1, total_downloads=1):
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

            print(f"  ✅ Downloaded successfully!")
            print(f"  📏 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            return filepath

        except Exception as e:
            print(f"  ❌ Failed to download PDF: {e}")
            import traceback

            print(f"  🔍 Traceback: {traceback.format_exc()}")
            return None

    def scrape_studies(self):
        """Main method to scrape studies and download PDFs"""
        downloaded_files = []

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
            all_pdf_links = []
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
            print(f"❌ Error during scraping: {e}")
            import traceback

            print(f"🔍 Traceback: {traceback.format_exc()}")
            return downloaded_files
        finally:
            if self.driver:
                print("🔒 Closing browser...")
                self.driver.quit()


def get_env_default(env_var, fallback, convert_type=None):
    """Helper to get environment variable with proper empty value handling"""
    value = os.getenv(env_var, "").strip()
    if not value:
        value = fallback

    if convert_type == int:
        return int(value)
    elif convert_type == bool:
        return value.lower() in ("true", "1", "yes", "on")
    return value


@click.command()
@click.option(
    "--email", "-e", help="Email for Wellbin login (overrides WELLBIN_EMAIL env var)"
)
@click.option(
    "--password",
    "-p",
    help="Password for Wellbin login (overrides WELLBIN_PASSWORD env var)",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    help="Limit number of studies to download, 0 = all (overrides WELLBIN_STUDY_LIMIT env var)",
)
@click.option(
    "--types",
    "-t",
    help='Study types to download: FhirStudy,DicomStudy or "all" (overrides WELLBIN_STUDY_TYPES env var)',
)
@click.option(
    "--output",
    "-o",
    help="Output directory for downloaded files (overrides WELLBIN_OUTPUT_DIR env var)",
)
@click.option(
    "--headless/--no-headless",
    help="Run browser in headless mode (overrides WELLBIN_HEADLESS env var)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be downloaded without actually downloading",
)
def main(email, password, limit, types, output, headless, dry_run):
    """
    Wellbin Medical Data Scraper

    Universal scraper for downloading medical data from Wellbin platform.
    Supports FhirStudy (lab reports) and DicomStudy (imaging reports) with proper categorization.

    ARGUMENT PRECEDENCE (highest to lowest):
    1. Command line arguments (--email, --limit, --types, etc.)
    2. Environment variables (WELLBIN_EMAIL, WELLBIN_STUDY_LIMIT, etc.)
    3. Built-in defaults

    Examples:
    \b
        # Download 5 lab reports
        uv run python wellbin_scrape_labs.py --limit 5 --types FhirStudy

        # Download all imaging studies
        uv run python wellbin_scrape_labs.py --limit 0 --types DicomStudy

        # Download both lab and imaging studies
        uv run python wellbin_scrape_labs.py --types FhirStudy,DicomStudy

        # Download everything
        uv run python wellbin_scrape_labs.py --types all

        # Dry run to see what would be downloaded
        uv run python wellbin_scrape_labs.py --dry-run --types DicomStudy
    """

    # PROPER PRECEDENCE: CLI args override env vars override defaults
    final_email = (
        email
        if email is not None
        else get_env_default("WELLBIN_EMAIL", "your-email@example.com")
    )
    final_password = (
        password
        if password is not None
        else get_env_default("WELLBIN_PASSWORD", "your-password")
    )
    final_limit = (
        limit if limit is not None else get_env_default("WELLBIN_STUDY_LIMIT", "0", int)
    )
    final_types = (
        types
        if types is not None
        else get_env_default("WELLBIN_STUDY_TYPES", "FhirStudy")
    )
    final_output = (
        output
        if output is not None
        else get_env_default("WELLBIN_OUTPUT_DIR", "medical_data")
    )

    # For boolean flags: True/False if provided, otherwise check env var, otherwise default
    if headless is not None:
        final_headless = headless
    else:
        final_headless = get_env_default("WELLBIN_HEADLESS", "true", bool)

    # Parse study types
    if final_types.lower() == "all":
        study_types = ["all"]
    else:
        study_types = [t.strip() for t in final_types.split(",")]

    # Convert limit
    if final_limit == 0:
        final_limit = None

    # Display configuration
    click.echo("🚀 Wellbin Medical Data Scraper")
    click.echo("=" * 50)
    click.echo(f"📧 Email: {final_email}")
    click.echo(
        f"🔢 Study limit: {final_limit if final_limit else 'No limit (all studies)'}"
    )
    click.echo(f"🎯 Study types: {', '.join(study_types)}")
    click.echo(f"📁 Output directory: {final_output}")
    click.echo(f"🤖 Headless mode: {final_headless}")
    if dry_run:
        click.echo("🔍 DRY RUN MODE: Will not download files")

    # Show precedence information
    click.echo("\n🔧 Argument Sources:")
    click.echo(f"   Email: {'CLI' if email else 'ENV/Default'}")
    click.echo(f"   Password: {'CLI' if password else 'ENV/Default'}")
    click.echo(f"   Limit: {'CLI' if limit is not None else 'ENV/Default'}")
    click.echo(f"   Types: {'CLI' if types else 'ENV/Default'}")
    click.echo(f"   Output: {'CLI' if output else 'ENV/Default'}")
    click.echo(f"   Headless: {'CLI' if headless is not None else 'ENV/Default'}")
    click.echo("=" * 50)

    if dry_run:
        click.echo("\n⚠️  This is a dry run. No files will be downloaded.")
        click.echo("Remove --dry-run flag to actually download files.")

    # Create and run scraper
    scraper = WellbinMedicalScraper(
        email=final_email,
        password=final_password,
        headless=final_headless,
        limit_studies=final_limit,
        study_types=study_types,
        output_dir=final_output,
    )

    if dry_run:
        # For dry run, we'd need to implement a dry run mode in the scraper
        click.echo("\n🔍 DRY RUN: Not implemented yet. Remove --dry-run to download.")
        return

    downloaded_files = scraper.scrape_studies()

    # Summary
    click.echo("\n" + "=" * 60)
    click.echo("🎉 SCRAPING COMPLETE!")
    click.echo("=" * 60)

    if downloaded_files:
        click.echo(f"✅ Successfully downloaded {len(downloaded_files)} files:")

        # Group by study type for summary
        by_type = {}
        for file_info in downloaded_files:
            study_type = file_info["study_type"]
            if study_type not in by_type:
                by_type[study_type] = []
            by_type[study_type].append(file_info)

        for study_type, files in by_type.items():
            config = scraper.study_config.get(
                study_type, {"icon": "📄", "description": study_type}
            )
            click.echo(
                f"\n{config['icon']} {config['description']} ({len(files)} files):"
            )
            for i, file_info in enumerate(files, 1):
                click.echo(f"  {i}. 📄 {file_info['local_path']}")
                click.echo(f"     📅 Study date: {file_info['study_date']}")
                click.echo(f"     📝 Description: {file_info['description']}")
    else:
        click.echo("❌ No files were downloaded")

    # Show organized directory structure
    if downloaded_files:
        click.echo(f"\n📁 Files organized in {final_output}/:")
        for study_type in by_type.keys():
            config = scraper.study_config.get(
                study_type, {"subdir": "unknown", "icon": "📄"}
            )
            file_count = len(by_type[study_type])
            click.echo(f"  {config['icon']} {config['subdir']}/  ({file_count} files)")


if __name__ == "__main__":
    main()
