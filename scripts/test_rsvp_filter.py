#!/usr/bin/env python3
"""
RSVP filtering and export script for Zola.

This script exports RSVPs filtered by side (Groom/Bride) to separate CSV files.
This approach avoids name collision issues when there are guests with the same
name on different sides (e.g., two "Dipti Patel" guests).

Workflow:
1. Open filter dropdown
2. Select all Groom filters (Mahek's categories)
3. Export RSVPs as CSV
4. Clear filters
5. Select all Bride filters (Saumya's categories)
6. Export RSVPs as CSV

Usage:
    python test_rsvp_filter.py
    python test_rsvp_filter.py --headless  # Run without visible browser
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

# URLs
TRACK_RSVPS_URL = "https://www.zola.com/wedding/manage/guests/rsvps/overview"

# Session file location
SESSION_FILE = Path(__file__).parent.parent / "data" / ".zola_session.json"

# Filter categories - these match the relationship names on Zola
GROOM_FILTERS = [
    "Mahek's wedding party",
    "Mahek's family",
    "Mahek's family friends",
    "Mahek's friends",
]

BRIDE_FILTERS = [
    "Saumya's wedding party",
    "Saumya's family",
    "Saumya's family friends",
    "Saumya's friends",
]


def get_session_from_file() -> dict | None:
    """Load session state from local file."""
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load session file: {e}")
    return None


def save_screenshot(page: Page, data_dir: Path, name: str):
    """Save a screenshot with the given name."""
    path = data_dir / f"{name}.png"
    page.screenshot(path=str(path))
    print(f"   📸 Screenshot: {name}.png")


def open_filter_dropdown(page: Page, data_dir: Path, prefix: str) -> bool:
    """Open the Filter Guests dropdown."""
    print("\n" + "="*50)
    print("Opening Filter Guests dropdown")
    print("="*50)

    save_screenshot(page, data_dir, f"{prefix}_before_open_dropdown")

    try:
        # Find the filter dropdown by looking for text containing "Filter Guests"
        # or "Filters Selected" (when filters are active)
        filter_dropdown = page.locator('a:has-text("Filter Guests"), a:has-text("Filters Selected")').first

        if filter_dropdown.count() == 0:
            # Fallback: try finding by the dropdown icon area
            filter_dropdown = page.locator('[class*="filter"] a, [class*="Filter"] a').first

        filter_dropdown.click(timeout=5000)
        print("   ✓ Clicked filter dropdown")
        page.wait_for_timeout(1000)
        save_screenshot(page, data_dir, f"{prefix}_after_open_dropdown")
        return True

    except Exception as e:
        print(f"   ✗ Failed to click filter dropdown: {e}")
        save_screenshot(page, data_dir, f"{prefix}_error_open_dropdown")
        return False


def select_filters(page: Page, data_dir: Path, filter_names: list[str], side_name: str) -> int:
    """Select checkboxes for the given filter names."""
    print("\n" + "="*50)
    print(f"Selecting {side_name} filters ({len(filter_names)} total)")
    print("="*50)

    selected_count = 0

    for i, filter_name in enumerate(filter_names):
        print(f"   Selecting: {filter_name}...", end=" ")

        try:
            # Strategy 1: Find label containing the filter name and click it
            # This is the most reliable approach based on our debugging
            label_selector = f'label:has-text("{filter_name}")'
            label = page.locator(label_selector).first

            if label.count() > 0:
                label.click(timeout=3000)
                selected_count += 1
                print("✓")
                page.wait_for_timeout(300)
                continue

            # Strategy 2: Find checkbox input with associated label
            checkbox_selector = f'input[type="checkbox"] + label:has-text("{filter_name}")'
            checkbox = page.locator(checkbox_selector).first

            if checkbox.count() > 0:
                checkbox.click(timeout=3000)
                selected_count += 1
                print("✓")
                page.wait_for_timeout(300)
                continue

            # Strategy 3: Find list item containing the filter name
            li_selector = f'li:has-text("{filter_name}")'
            li_element = page.locator(li_selector).first

            if li_element.count() > 0:
                li_element.click(timeout=3000)
                selected_count += 1
                print("✓")
                page.wait_for_timeout(300)
                continue

            print(f"✗ (not found)")
            save_screenshot(page, data_dir, f"{side_name.lower()}_error_select_{i}")

        except PlaywrightTimeout:
            print(f"✗ (timeout)")
            save_screenshot(page, data_dir, f"{side_name.lower()}_error_select_{i}")
        except Exception as e:
            print(f"✗ ({str(e)[:40]})")
            save_screenshot(page, data_dir, f"{side_name.lower()}_error_select_{i}")

    print(f"\n   Selected {selected_count} of {len(filter_names)} filters")
    save_screenshot(page, data_dir, f"{side_name.lower()}_after_all_selections")
    return selected_count


def export_rsvps(page: Page, data_dir: Path, download_dir: Path, filename: str, prefix: str) -> Path | None:
    """Click Export RSVPs and download CSV."""
    print("\n" + "="*50)
    print(f"Exporting RSVPs to {filename}")
    print("="*50)

    # First close the filter dropdown by clicking elsewhere or pressing Escape
    print("   Closing filter dropdown...")
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    # Click somewhere neutral to ensure dropdown is closed
    page.locator('h1, h2, [class*="header"]').first.click(force=True)
    page.wait_for_timeout(500)
    save_screenshot(page, data_dir, f"{prefix}_after_close_dropdown")

    # Click Export RSVPs button
    print("   Looking for Export RSVPs button...")

    try:
        # Find and click the Export RSVPs button
        export_button = page.locator('button:has-text("Export")').first
        export_button.click(timeout=5000)
        print("   ✓ Clicked Export RSVPs button")
    except Exception as e:
        print(f"   ✗ Could not find Export RSVPs button: {e}")
        save_screenshot(page, data_dir, f"{prefix}_error_no_export_button")
        return None

    # Wait for dropdown menu to appear
    page.wait_for_timeout(1000)
    save_screenshot(page, data_dir, f"{prefix}_export_dropdown_open")

    # Click CSV format option and wait for download
    print("   Clicking CSV format option...")

    try:
        with page.expect_download(timeout=30000) as download_info:
            # Find and click the .csv format option
            csv_option = page.locator('a:has-text(".csv format"), text=".csv format"').first
            csv_option.click(timeout=5000)
            print("   ✓ Clicked CSV option")

        download = download_info.value
        output_path = download_dir / filename
        download.save_as(output_path)
        print(f"   ✓ Saved to: {output_path}")
        save_screenshot(page, data_dir, f"{prefix}_after_download")
        return output_path

    except PlaywrightTimeout:
        print("   ✗ Download timed out")
        save_screenshot(page, data_dir, f"{prefix}_error_download_timeout")
        return None
    except Exception as e:
        print(f"   ✗ Export failed: {e}")
        save_screenshot(page, data_dir, f"{prefix}_error_export")
        return None


def clear_filters(page: Page, data_dir: Path) -> bool:
    """Open filter dropdown and click Clear button."""
    print("\n" + "="*50)
    print("Clearing all filters")
    print("="*50)

    save_screenshot(page, data_dir, "clear_step_before")

    # First open the filter dropdown
    print("   Opening filter dropdown...")
    try:
        filter_dropdown = page.locator('a:has-text("Filters Selected")').first
        filter_dropdown.click(timeout=5000)
        print("   ✓ Opened filter dropdown")
        page.wait_for_timeout(1000)
        save_screenshot(page, data_dir, "clear_step_dropdown_open")
    except Exception as e:
        print(f"   ✗ Failed to open dropdown: {e}")
        save_screenshot(page, data_dir, "clear_step_error_open")
        return False

    # Click the Clear button
    print("   Clicking Clear button...")
    try:
        clear_button = page.locator('button:has-text("Clear")').first
        clear_button.click(timeout=5000)
        print("   ✓ Clicked Clear button")
        page.wait_for_timeout(1000)
        save_screenshot(page, data_dir, "clear_step_after_clear")
        return True
    except Exception as e:
        print(f"   ✗ Failed to click Clear: {e}")
        save_screenshot(page, data_dir, "clear_step_error_clear")
        return False


def verify_filter_count(page: Page, expected_count: int) -> bool:
    """Verify the expected number of filters are selected."""
    try:
        filter_text = page.locator('a:has-text("Filters Selected")').first.text_content()
        if filter_text and str(expected_count) in filter_text:
            print(f"   ✓ Verified: {expected_count} filters selected")
            return True
        else:
            print(f"   ⚠ Filter count mismatch: expected {expected_count}, got '{filter_text}'")
            return False
    except:
        return False


def main():
    parser = argparse.ArgumentParser(description="Export filtered RSVPs from Zola")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--keep-open", type=int, default=5, help="Seconds to keep browser open after completion")
    args = parser.parse_args()

    # Check for session
    session_state = get_session_from_file()
    if not session_state:
        print("ERROR: No saved session found.")
        print("Run: python download_zola_data.py --save-session")
        sys.exit(1)

    # Setup directories
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    download_dir = data_dir / "raw"
    download_dir.mkdir(parents=True, exist_ok=True)

    # Timestamp for filenames
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    print("="*60)
    print("ZOLA RSVP FILTERED EXPORT")
    print("="*60)
    print(f"Download directory: {download_dir}")
    print(f"Timestamp: {timestamp}")
    print(f"Headless mode: {args.headless}")

    with sync_playwright() as p:
        print("\nLaunching browser...")
        browser = p.chromium.launch(headless=args.headless)

        context = browser.new_context(
            storage_state=session_state,
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
        )
        page = context.new_page()

        try:
            # Navigate to Track RSVPs page
            print("\nNavigating to Track RSVPs page...")
            page.goto(TRACK_RSVPS_URL)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # Check if we're logged in
            if "login" in page.url.lower():
                print("ERROR: Session expired. Please run --save-session again.")
                browser.close()
                sys.exit(1)

            print(f"Current URL: {page.url}")

            # Initial screenshot
            save_screenshot(page, data_dir, "00_initial_page")

            # ============================================
            # GROOM'S SIDE EXPORT
            # ============================================
            print("\n" + "#"*60)
            print("# GROOM'S SIDE EXPORT")
            print("#"*60)

            # Open filter dropdown
            if not open_filter_dropdown(page, data_dir, "groom_01"):
                raise Exception("Failed to open filter dropdown (Groom)")

            # Select Groom filters
            groom_selected = select_filters(page, data_dir, GROOM_FILTERS, "Groom")

            if groom_selected < len(GROOM_FILTERS):
                print(f"\n   ⚠ Warning: Only {groom_selected}/{len(GROOM_FILTERS)} filters selected")

            # Export RSVPs
            groom_file = export_rsvps(
                page, data_dir, download_dir,
                f"groom_rsvps_{timestamp}.csv", "groom_03"
            )

            # ============================================
            # CLEAR FILTERS
            # ============================================
            print("\n" + "#"*60)
            print("# CLEARING FILTERS")
            print("#"*60)

            if not clear_filters(page, data_dir):
                print("\n   Clear failed - refreshing page instead...")
                page.reload()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)
                save_screenshot(page, data_dir, "clear_after_refresh")

            # ============================================
            # BRIDE'S SIDE EXPORT
            # ============================================
            print("\n" + "#"*60)
            print("# BRIDE'S SIDE EXPORT")
            print("#"*60)

            # Open filter dropdown
            if not open_filter_dropdown(page, data_dir, "bride_01"):
                raise Exception("Failed to open filter dropdown (Bride)")

            # Select Bride filters
            bride_selected = select_filters(page, data_dir, BRIDE_FILTERS, "Bride")

            if bride_selected < len(BRIDE_FILTERS):
                print(f"\n   ⚠ Warning: Only {bride_selected}/{len(BRIDE_FILTERS)} filters selected")

            # Export RSVPs
            bride_file = export_rsvps(
                page, data_dir, download_dir,
                f"bride_rsvps_{timestamp}.csv", "bride_03"
            )

            # ============================================
            # SUMMARY
            # ============================================
            print("\n" + "="*60)
            print("EXPORT COMPLETE")
            print("="*60)

            if groom_file:
                print(f"✓ Groom RSVPs: {groom_file}")
            else:
                print("✗ Groom RSVPs: FAILED")

            if bride_file:
                print(f"✓ Bride RSVPs: {bride_file}")
            else:
                print("✗ Bride RSVPs: FAILED")

            if groom_file and bride_file:
                print("\n✓ Both exports successful!")
                print(f"\nNext step: Run the combine script:")
                print(f"  python scripts/combine_side_exports.py")
            else:
                print("\n✗ Some exports failed - check the screenshots for debugging")

            # Keep browser open for inspection if not headless
            if not args.headless and args.keep_open > 0:
                print(f"\nBrowser will stay open for {args.keep_open} seconds for inspection...")
                time.sleep(args.keep_open)

        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"\nERROR: {e}")
            screenshot_path = data_dir / "error_screenshot.png"
            page.screenshot(path=str(screenshot_path))
            print(f"Error screenshot saved: {screenshot_path}")
            raise
        finally:
            print("\nClosing browser...")
            browser.close()


if __name__ == "__main__":
    main()
