#!/usr/bin/env python3
"""
Zola Data Downloader

Automates downloading RSVP and Guest List data from Zola.com using Playwright.
Includes automatic OTP fetching from Gmail.

Usage:
    python download_zola_data.py

Environment Variables (required):
    ZOLA_EMAIL         - Your email (used for both Zola login and Gmail OTP)
    ZOLA_PASSWORD      - Your Zola account password
    GMAIL_APP_PASSWORD - Your Gmail App Password (16 chars, no spaces)

For GitHub Actions, store these as repository secrets.
"""

import os
import sys
import imaplib
import email
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


# Configuration
ZOLA_LOGIN_URL = "https://www.zola.com/account/login"
GUEST_LIST_URL = "https://www.zola.com/wedding/manage/guests/all"
TRACK_RSVPS_URL = "https://www.zola.com/wedding/manage/guests/rsvps/overview"

# Gmail IMAP settings
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_IMAP_PORT = 993


def get_credentials() -> tuple[str, str, str]:
    """Get all credentials from environment variables."""
    email = os.environ.get("ZOLA_EMAIL")
    zola_password = os.environ.get("ZOLA_PASSWORD")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not email or not zola_password:
        print("ERROR: ZOLA_EMAIL and ZOLA_PASSWORD environment variables are required.")
        sys.exit(1)

    if not gmail_app_password:
        print("ERROR: GMAIL_APP_PASSWORD environment variable is required for OTP.")
        print("\nSet it with:")
        print("  export GMAIL_APP_PASSWORD='xxxxxxxxxxxx'  # 16-char app password, no spaces")
        sys.exit(1)

    # Remove spaces from app password if any
    gmail_app_password = gmail_app_password.replace(" ", "")

    return email, zola_password, gmail_app_password


def setup_directories(data_dir: Path) -> Path:
    """Ensure directories exist and return download path."""
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir


def fetch_otp_from_gmail(gmail_email: str, gmail_app_password: str, max_wait_seconds: int = 60) -> str | None:
    """
    Fetch the latest OTP code from Zola email in Gmail.

    Args:
        gmail_email: Gmail address
        gmail_app_password: Gmail app password
        max_wait_seconds: Maximum time to wait for OTP email

    Returns:
        OTP code string or None if not found
    """
    print(f"Connecting to Gmail to fetch OTP...")
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL(GMAIL_IMAP_SERVER, GMAIL_IMAP_PORT)
            mail.login(gmail_email, gmail_app_password)
            mail.select("INBOX")

            # Search for recent emails from Zola
            # Look for emails from the last 5 minutes
            date_since = (datetime.now() - timedelta(minutes=5)).strftime("%d-%b-%Y")
            search_criteria = f'(FROM "zola" SINCE "{date_since}")'

            _, message_numbers = mail.search(None, search_criteria)

            if not message_numbers[0]:
                print(f"  No Zola emails found yet, waiting... ({int(time.time() - start_time)}s)")
                mail.logout()
                time.sleep(5)
                continue

            # Get the most recent email
            latest_email_id = message_numbers[0].split()[-1]
            _, msg_data = mail.fetch(latest_email_id, "(RFC822)")

            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            # Extract email content
            body_text = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    elif part.get_content_type() == "text/html":
                        body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                body_text = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')

            # Look for OTP patterns (usually 4-6 digit codes)
            # Common patterns: "code is 123456", "verification code: 123456", "OTP: 123456"
            otp_patterns = [
                r'(?:code|otp|verification)[:\s]+(\d{4,6})',
                r'(\d{6})\s*(?:is your|verification)',
                r'(?:enter|use)\s+(\d{4,6})',
                r'\b(\d{6})\b',  # Fallback: any 6-digit number
            ]

            for pattern in otp_patterns:
                match = re.search(pattern, body_text, re.IGNORECASE)
                if match:
                    otp = match.group(1)
                    print(f"  Found OTP: {otp}")
                    mail.logout()
                    return otp

            print(f"  Email found but no OTP pattern matched, waiting...")
            mail.logout()
            time.sleep(5)

        except imaplib.IMAP4.error as e:
            print(f"  IMAP error: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"  Error fetching email: {e}")
            time.sleep(5)

    print("ERROR: Timed out waiting for OTP email")
    return None


def login_to_zola(page, email: str, zola_password: str, gmail_app_password: str, data_dir: Path) -> bool:
    """Login to Zola.com, handling OTP if required."""
    print("Navigating to Zola login page...")
    page.goto(ZOLA_LOGIN_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # Take screenshot of login page for debugging
    page.screenshot(path=str(data_dir / "debug_1_login_page.png"))
    print("Screenshot: debug_1_login_page.png")

    print("Entering credentials...")
    print(f"  Email: {email[:3]}***{email[-10:]}")  # Partial email for debugging

    # Try multiple selectors for email input
    email_selectors = ['input[name="email"]', 'input[type="email"]', '#email']
    for selector in email_selectors:
        try:
            if page.locator(selector).count() > 0:
                page.fill(selector, email)
                print(f"  Filled email with: {selector}")
                break
        except:
            continue

    # Try multiple selectors for password input
    password_selectors = ['input[name="password"]', 'input[type="password"]', '#password']
    for selector in password_selectors:
        try:
            if page.locator(selector).count() > 0:
                page.fill(selector, zola_password)
                print(f"  Filled password with: {selector}")
                break
        except:
            continue

    # Take screenshot after filling credentials
    page.screenshot(path=str(data_dir / "debug_2_credentials_filled.png"))
    print("Screenshot: debug_2_credentials_filled.png")

    # Click login button
    print("Clicking login button...")
    submit_selectors = ['button[type="submit"]', 'button:has-text("Log in")', 'button:has-text("Sign in")']
    for selector in submit_selectors:
        try:
            if page.locator(selector).count() > 0:
                page.click(selector)
                print(f"  Clicked: {selector}")
                break
        except:
            continue

    # Wait for page to respond
    page.wait_for_timeout(5000)

    # Take screenshot after login attempt
    page.screenshot(path=str(data_dir / "debug_3_after_login_click.png"))
    print(f"Screenshot: debug_3_after_login_click.png")
    print(f"Current URL: {page.url}")

    # Check if OTP is required
    otp_selectors = [
        'input[name="otp"]',
        'input[name="code"]',
        'input[name="verificationCode"]',
        'input[placeholder*="code"]',
        'input[placeholder*="OTP"]',
        'input[type="tel"]',  # OTP inputs are often type="tel"
        '[data-testid*="otp"]',
        '[data-testid*="code"]',
    ]

    otp_input = None
    for selector in otp_selectors:
        try:
            if page.locator(selector).count() > 0:
                otp_input = page.locator(selector).first
                print(f"OTP input detected with selector: {selector}")
                break
        except:
            continue

    # Also check for text indicating OTP is needed
    if not otp_input:
        page_text = page.content().lower()
        if any(phrase in page_text for phrase in ["verification code", "enter code", "check your email", "otp", "one-time"]):
            print("OTP page detected by text content")
            # Try to find any visible input
            otp_input = page.locator('input:visible').first

    if otp_input:
        print("\n--- OTP Required ---")

        # Fetch OTP from Gmail
        otp_code = fetch_otp_from_gmail(email, gmail_app_password)

        if not otp_code:
            print("ERROR: Could not retrieve OTP from email")
            return False

        # Enter OTP
        print(f"Entering OTP: {otp_code}")
        otp_input.fill(otp_code)

        # Look for submit/verify button
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Verify")',
            'button:has-text("Submit")',
            'button:has-text("Continue")',
            'button:has-text("Confirm")',
        ]

        for selector in submit_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.click(selector, timeout=3000)
                    print(f"Clicked submit with: {selector}")
                    break
            except:
                continue

        # Wait for navigation after OTP
        page.wait_for_timeout(3000)

    # Verify login success
    try:
        page.wait_for_url("**/wedding/**", timeout=15000)
        print("Login successful!")
        return True
    except PlaywrightTimeout:
        current_url = page.url
        if "login" in current_url or "auth" in current_url:
            print(f"ERROR: Login failed. Still on: {current_url}")
            return False
        print(f"Redirected to: {current_url}")
        return True


def download_guest_list(page, download_dir: Path, date_str: str) -> Path | None:
    """Download the Guest List CSV from Manage Guest List page."""
    print("\n--- Downloading Guest List ---")
    print("Navigating to Manage Guest List...")
    page.goto(GUEST_LIST_URL)
    page.wait_for_load_state("networkidle")

    # Wait for the table to load
    page.wait_for_selector("text=Name", timeout=10000)
    page.wait_for_timeout(2000)  # Extra wait for page to fully render

    # Click the three dots menu
    print("Looking for export menu...")

    # XPath provided by user for the three dots button
    user_xpath = "/html/body/div[1]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div/div/div/div[2]/div[1]/div[1]/div/div/div/div[1]/div/button"

    three_dots_selectors = [
        # User's XPath first
        f"xpath={user_xpath}",
        # SVG with three dots/ellipsis pattern
        'button:has(svg path[d*="M12"])',
        'button svg >> xpath=..',
        # Buttons in the header area
        '[class*="header"] button:has(svg)',
        '[class*="Header"] button:has(svg)',
        # Any button with ellipsis-like attributes
        'button[aria-haspopup="true"]',
        'button[aria-expanded]',
        # Generic: find button with SVG near the table header
        'div:has(> div:text("Name")) button:has(svg)',
    ]

    menu_clicked = False
    for selector in three_dots_selectors:
        try:
            print(f"  Trying: {selector[:60]}...")
            if selector.startswith('xpath='):
                locator = page.locator(selector)
            else:
                locator = page.locator(selector)

            if locator.count() > 0:
                locator.first.click(timeout=3000)
                menu_clicked = True
                print(f"  SUCCESS: Clicked menu with selector")
                break
        except Exception as e:
            print(f"  Failed: {str(e)[:50]}")
            continue

    if not menu_clicked:
        # Last resort: try to find any clickable element with "..." text or icon
        print("  Trying last resort selectors...")
        try:
            # Look for the button by its position - it should be in the table header row
            page.locator('button').filter(has=page.locator('svg')).first.click(timeout=5000)
            menu_clicked = True
            print("  SUCCESS: Clicked first button with SVG")
        except:
            pass

    if not menu_clicked:
        raise Exception("Could not find the three dots export menu button")

    # Wait for dropdown menu to appear
    page.wait_for_timeout(1000)

    # Start waiting for download before clicking
    print("Clicking CSV export option...")
    with page.expect_download(timeout=30000) as download_info:
        # Try multiple text variations
        csv_selectors = [
            'text="Export .csv format"',
            'text="Export CSV format"',
            'text=".csv format"',
            'text="csv format"',
            ':text-is("Export .csv format")',
        ]
        clicked = False
        for selector in csv_selectors:
            try:
                page.click(selector, timeout=3000)
                clicked = True
                print(f"  Clicked: {selector}")
                break
            except:
                continue
        if not clicked:
            raise Exception("Could not find CSV export option in dropdown")

    download = download_info.value
    output_path = download_dir / f"guest_list_{date_str}.csv"
    download.save_as(output_path)
    print(f"Saved Guest List to: {output_path}")
    return output_path


def download_rsvps(page, download_dir: Path, date_str: str) -> Path | None:
    """Download the RSVPs CSV from Track RSVPs page."""
    print("\n--- Downloading RSVPs ---")
    print("Navigating to Track RSVPs...")
    page.goto(TRACK_RSVPS_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)  # Extra wait for page to fully render

    # Click "Export RSVPs" dropdown button
    print("Clicking Export RSVPs button...")

    export_selectors = [
        'button:has-text("Export RSVPs")',
        'text="Export RSVPs"',
        ':text("Export RSVPs")',
        'button:text-is("Export RSVPs")',
        '[class*="export"] button',
        'button >> text=Export',
    ]

    clicked = False
    for selector in export_selectors:
        try:
            print(f"  Trying: {selector}")
            if page.locator(selector).count() > 0:
                page.locator(selector).first.click(timeout=5000)
                clicked = True
                print(f"  SUCCESS: Clicked Export RSVPs button")
                break
        except Exception as e:
            print(f"  Failed: {str(e)[:40]}")
            continue

    if not clicked:
        raise Exception("Could not find Export RSVPs button")

    # Wait for dropdown to appear
    page.wait_for_timeout(1000)

    # Start waiting for download before clicking
    print("Clicking CSV format option...")
    with page.expect_download(timeout=30000) as download_info:
        # Try multiple text variations
        csv_selectors = [
            'text=".csv format"',
            'text="Export .csv format"',
            'text="csv format"',
        ]
        clicked = False
        for selector in csv_selectors:
            try:
                page.click(selector, timeout=3000)
                clicked = True
                print(f"  Clicked: {selector}")
                break
            except:
                continue
        if not clicked:
            raise Exception("Could not find CSV export option in dropdown")

    download = download_info.value
    output_path = download_dir / f"rsvps_{date_str}.csv"
    download.save_as(output_path)
    print(f"Saved RSVPs to: {output_path}")
    return output_path


def main():
    # Get credentials (email is used for both Zola and Gmail)
    email, zola_password, gmail_app_password = get_credentials()

    # Setup directories
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    download_dir = setup_directories(data_dir)

    # Date string for filenames
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Download date: {date_str}")
    print(f"Download directory: {download_dir}")

    # Launch browser
    with sync_playwright() as p:
        print("\nLaunching browser...")
        browser = p.chromium.launch(
            headless=os.environ.get("HEADLESS", "true").lower() == "true"
        )
        context = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        try:
            # Login (with OTP handling)
            if not login_to_zola(page, email, zola_password, gmail_app_password, data_dir):
                browser.close()
                sys.exit(1)

            # Download Guest List
            guest_list_path = download_guest_list(page, download_dir, date_str)

            # Download RSVPs
            rsvps_path = download_rsvps(page, download_dir, date_str)

            print("\n" + "="*50)
            print("DOWNLOAD COMPLETE")
            print("="*50)
            if guest_list_path:
                print(f"Guest List: {guest_list_path}")
            if rsvps_path:
                print(f"RSVPs: {rsvps_path}")

        except Exception as e:
            print(f"\nERROR: {e}")
            # Take a screenshot for debugging
            screenshot_path = data_dir / "error_screenshot.png"
            page.screenshot(path=str(screenshot_path))
            print(f"Screenshot saved to: {screenshot_path}")
            raise

        finally:
            browser.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
