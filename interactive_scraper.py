#!/usr/bin/env python3
"""
Interactive Wellbin Web Scraper
A script that allows user guidance during the scraping process
"""

import os
import time
import urllib.parse

import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class InteractiveWellbinScraper:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.login_url = "https://wellbin.co/login"
        self.session = requests.Session()
        self.driver = None
        self.wait = None

    def setup_driver(self):
        """Setup Chrome driver - always visible for interaction"""
        chrome_options = Options()
        # Keep browser visible for interaction
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1400,1000")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)

    def wait_for_user_input(self, message):
        """Pause and wait for user guidance"""
        print(f"\n{'='*60}")
        print(f"🔍 {message}")
        print(f"{'='*60}")
        return (
            input("Press Enter to continue, or type 'quit' to exit: ").strip().lower()
        )

    def login(self):
        """Login to Wellbin with user guidance"""
        try:
            print("Setting up browser (this will open a Chrome window)...")
            self.setup_driver()

            print("Navigating to login page...")
            self.driver.get(self.login_url)
            time.sleep(2)

            if (
                self.wait_for_user_input(
                    "I'm now on the login page. You should see the Chrome window open."
                )
                == "quit"
            ):
                return False

            # Find and fill email
            email_field = self.driver.find_element(
                By.CSS_SELECTOR, "input[type='email']"
            )
            email_field.clear()
            email_field.send_keys(self.email)

            # Find and fill password
            password_field = self.driver.find_element(
                By.CSS_SELECTOR, "input[type='password']"
            )
            password_field.clear()
            password_field.send_keys(self.password)

            if (
                self.wait_for_user_input(
                    "I've filled in the login credentials. Check if they look correct."
                )
                == "quit"
            ):
                return False

            # Submit form
            submit_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[type='submit']"
            )
            submit_button.click()

            time.sleep(3)

            if "dashboard" in self.driver.current_url.lower():
                print("✅ Login successful! We're on the dashboard.")
                return True
            else:
                print("❌ Login may have failed. Current URL:", self.driver.current_url)
                return False

        except Exception as e:
            print(f"Error during login: {e}")
            return False

    def explore_with_guidance(self):
        """Interactive exploration with user guidance"""
        try:
            if not self.login():
                print("Login failed, cannot proceed")
                return

            print(f"\n🎉 Successfully logged in!")
            print(f"Current URL: {self.driver.current_url}")
            print(f"Page Title: {self.driver.title}")

            while True:
                current_url = self.driver.current_url
                print(f"\n📍 Current location: {current_url}")

                # Show available links
                links = self.driver.find_elements(By.TAG_NAME, "a")
                visible_links = []

                for link in links:
                    try:
                        if link.is_displayed() and link.text.strip():
                            href = link.get_attribute("href")
                            text = link.text.strip()
                            if href and text:
                                visible_links.append((text, href))
                    except:
                        pass

                print("\n🔗 Available links on this page:")
                for i, (text, href) in enumerate(visible_links[:10], 1):
                    print(f"  {i}. {text} -> {href}")

                # Check for potential PDF/file links
                pdf_patterns = [
                    "//a[contains(@href, '.pdf')]",
                    "//a[contains(text(), 'PDF')]",
                    "//a[contains(text(), 'Descargar')]",
                    "//a[contains(text(), 'Download')]",
                    "//a[contains(@href, 'download')]",
                ]

                pdf_links = []
                for pattern in pdf_patterns:
                    try:
                        elements = self.driver.find_elements(By.XPATH, pattern)
                        for element in elements:
                            if element.is_displayed():
                                href = element.get_attribute("href")
                                text = element.text.strip() or "PDF Link"
                                if href:
                                    pdf_links.append((text, href))
                    except:
                        pass

                if pdf_links:
                    print("\n📄 Found potential PDF/download links:")
                    for i, (text, href) in enumerate(pdf_links, 1):
                        print(f"  PDF {i}. {text} -> {href}")

                # Ask user for guidance
                print("\n" + "=" * 60)
                print("GUIDANCE NEEDED:")
                print("- Look at the browser window")
                print("- Tell me what you see and where to go next")
                print("- Available commands:")
                print("  'explorer' - navigate to explorer page")
                print("  'timeline' - navigate to timeline page")
                print("  'profile' - navigate to profile page")
                print("  'click:TEXT' - click on link containing TEXT")
                print("  'download' - download any PDF links found")
                print("  'inspect' - show page structure")
                print("  'quit' - exit")
                print("=" * 60)

                user_input = input("What should I do next? ").strip().lower()

                if user_input == "quit":
                    break
                elif user_input == "explorer":
                    self.driver.get("https://wellbin.co/explorer")
                    time.sleep(2)
                elif user_input == "timeline":
                    self.driver.get("https://wellbin.co/timeline")
                    time.sleep(2)
                elif user_input == "profile":
                    self.driver.get("https://wellbin.co/profile")
                    time.sleep(2)
                elif user_input.startswith("click:"):
                    link_text = user_input[6:]
                    self.click_link_by_text(link_text)
                elif user_input == "download":
                    self.download_found_files(pdf_links)
                elif user_input == "inspect":
                    self.inspect_page()
                else:
                    print(f"Unknown command: {user_input}")

        except Exception as e:
            print(f"Error during exploration: {e}")
        finally:
            input("\nPress Enter to close the browser...")
            if self.driver:
                self.driver.quit()

    def click_link_by_text(self, text):
        """Click a link containing the specified text"""
        try:
            link = self.driver.find_element(
                By.XPATH, f"//a[contains(text(), '{text}')]"
            )
            print(f"Clicking link with text: {text}")
            link.click()
            time.sleep(2)
            print(f"Navigated to: {self.driver.current_url}")
        except Exception as e:
            print(f"Could not find or click link with text '{text}': {e}")

    def inspect_page(self):
        """Show detailed page structure"""
        print("\n" + "=" * 60)
        print("PAGE INSPECTION")
        print("=" * 60)

        # All clickable elements
        clickables = self.driver.find_elements(By.XPATH, "//a | //button")
        print(f"\n🖱️  Clickable elements ({len(clickables)}):")
        for i, element in enumerate(clickables[:15], 1):
            try:
                if element.is_displayed():
                    tag = element.tag_name
                    text = element.text.strip()[:50]
                    href = (
                        element.get_attribute("href")
                        or element.get_attribute("onclick")
                        or ""
                    )
                    print(f"  {i}. {tag}: '{text}' -> {href[:60]}")
            except:
                pass

        # All images
        images = self.driver.find_elements(By.TAG_NAME, "img")
        print(f"\n🖼️  Images ({len(images)}):")
        for i, img in enumerate(images[:10], 1):
            try:
                if img.is_displayed():
                    src = img.get_attribute("src")
                    alt = img.get_attribute("alt") or "No alt text"
                    print(f"  {i}. {alt[:30]} -> {src[:60]}")
            except:
                pass

        # Check for file-related content
        file_elements = self.driver.find_elements(
            By.XPATH,
            "//*[contains(text(), 'pdf') or contains(text(), 'PDF') or contains(text(), 'archivo') or contains(text(), 'file') or contains(text(), 'estudio') or contains(text(), 'download') or contains(text(), 'Descargar')]",
        )
        print(f"\n📄 File-related content ({len(file_elements)}):")
        for i, element in enumerate(file_elements[:10], 1):
            try:
                if element.is_displayed():
                    text = element.text.strip()[:60]
                    tag = element.tag_name
                    print(f"  {i}. {tag}: '{text}'")
            except:
                pass

        print("=" * 60)

    def download_found_files(self, pdf_links):
        """Download the PDF files that were found"""
        if not pdf_links:
            print("No PDF links found to download")
            return

        print(f"\n📥 Downloading {len(pdf_links)} files...")
        os.makedirs("downloads", exist_ok=True)

        # Get cookies for authenticated downloads
        selenium_cookies = self.driver.get_cookies()
        for cookie in selenium_cookies:
            self.session.cookies.set(cookie["name"], cookie["value"])

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.driver.current_url,
        }

        for i, (text, url) in enumerate(pdf_links, 1):
            try:
                print(f"Downloading {i}/{len(pdf_links)}: {text}")
                response = self.session.get(url, headers=headers, stream=True)
                response.raise_for_status()

                # Extract filename
                filename = f"wellbin_file_{i}.pdf"
                if "Content-Disposition" in response.headers:
                    cd = response.headers["Content-Disposition"]
                    if "filename=" in cd:
                        filename = cd.split("filename=")[1].strip('"')
                else:
                    filename = (
                        os.path.basename(urllib.parse.urlparse(url).path) or filename
                    )

                filepath = os.path.join("downloads", filename)
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"✅ Downloaded: {filepath}")

            except Exception as e:
                print(f"❌ Failed to download {text}: {e}")


def main():
    """Main interactive function"""
    email = "feniix@gmail.com"
    password = "Rem60tht"

    print("🚀 Starting Interactive Wellbin Scraper")
    print("=====================================")
    print("This will open a Chrome browser window that you can see and interact with.")
    print("I'll pause at key points for your guidance on where to find the PDF files.")
    print()

    scraper = InteractiveWellbinScraper(email, password)
    scraper.explore_with_guidance()


if __name__ == "__main__":
    main()
