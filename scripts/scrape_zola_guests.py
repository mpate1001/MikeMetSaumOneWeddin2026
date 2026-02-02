#!/usr/bin/env python3
"""
Scrape guest data directly from Zola website.

This script opens each guest's modal and extracts:
1. Guest Info: Names (primary, partner, children), Relationship (side)
2. RSVP Status: Response for each event

This approach is necessary because Zola's CSV export ignores filters
and doesn't include relationship data alongside RSVP status.

IMPORTANT: This script is READ-ONLY. It only clicks on:
- Guest names (to open modal)
- Tab headers (Guest Info, RSVP Status)
- Close button (X) to close modal

It NEVER clicks on dropdowns, inputs, or anything that could modify data.

Usage:
    python scrape_zola_guests.py
    python scrape_zola_guests.py --headless
    python scrape_zola_guests.py --limit 10  # Test with first 10 guests
"""

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Locator, TimeoutError as PlaywrightTimeout


@dataclass
class FailedGuest:
    """Track a failed guest scrape attempt."""
    index: int
    display_name: str
    reason: str
    attempts: int = 1

    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'display_name': self.display_name,
            'reason': self.reason,
            'attempts': self.attempts,
        }


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_immediate_retries: int = 3  # Retries per guest before moving on
    retry_pass_enabled: bool = True  # Do a final retry pass for all failures
    retry_pass_max_attempts: int = 2  # Attempts per guest in retry pass
    base_delay_ms: int = 800  # Base delay between operations
    retry_delay_multiplier: float = 1.5  # Increase delay on each retry
    max_acceptable_failures: int = 5  # Fail the run if more than this many guests fail
    slow_mode_delay_ms: int = 2000  # Delay for retry pass (slower)

# URLs
GUEST_LIST_URL = "https://www.zola.com/wedding/manage/guests/all"

# Session file location
SESSION_FILE = Path(__file__).parent.parent / "data" / ".zola_session.json"

# Events to scrape (in order they appear on Zola)
EVENTS = [
    "Mahek's Vidhi & Haaldi",
    "Saumya's Vidhi & Haaldi",
    "Wedding",
    "Reception",
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
    """Save a screenshot for debugging."""
    path = data_dir / "screenshots" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path))


def get_text_content(locator: Locator) -> str:
    """Safely get text content from a locator."""
    try:
        if locator.count() > 0:
            return (locator.first.text_content() or '').strip()
    except:
        pass
    return ''


def get_input_value(locator: Locator) -> str:
    """Safely get input value from a locator."""
    try:
        if locator.count() > 0:
            return (locator.first.input_value() or '').strip()
    except:
        pass
    return ''


def extract_guest_info_from_modal(page: Page) -> dict:
    """
    Extract guest information from the Guest Info tab of the modal.

    Based on observed structure:
    - Primary guest: textboxes with first/last name
    - Partner: additional textboxes for partner first/last name
    - Relationship: A generic element containing the dropdown, first child shows current value
    """
    info = {
        'primary_first': '',
        'primary_last': '',
        'partner_first': '',
        'partner_last': '',
        'relationship': '',
        'children': [],
        'events_invited': [],
    }

    try:
        modal = page.locator('dialog, [role="dialog"]').first

        # Get names using JavaScript for more reliable extraction
        names_data = page.evaluate('''() => {
            const modal = document.querySelector('.modal-content, dialog, [role="dialog"]');
            if (!modal) return { all_values: [] };

            const textboxes = modal.querySelectorAll('input[type="text"]');
            const values = Array.from(textboxes).map(t => t.value.trim());

            // Structure: Primary First, Primary Last, Suffix, Partner First, Partner Last, Suffix
            return {
                all_values: values,
                count: values.length
            };
        }''')

        all_values = names_data.get('all_values', [])
        print(f"      Textbox values ({len(all_values)}): {all_values[:8]}")

        # Assign names based on textbox values
        # Structure: [0]=First, [1]=Last, [2]=Suffix, [3]=empty?, [4]=Partner First, [5]=Partner Last, [6]=Suffix, [7]=empty?
        if len(all_values) >= 2:
            info['primary_first'] = all_values[0] or ''
            info['primary_last'] = all_values[1] or ''
        if len(all_values) >= 6:
            # Partner is at indices 4 and 5
            info['partner_first'] = all_values[4] or ''
            info['partner_last'] = all_values[5] or ''

        # Get relationship - the dropdown structure has:
        # label "Relationship To You"
        # A container with children where first child shows selected value
        #
        # Known relationship patterns to look for
        relationship_patterns = [
            "Saumya's Family Friend",
            "Saumya's Friend",
            "Saumya's Family",
            "Saumya's Wedding Party",
            "Mahek's Family Friend",
            "Mahek's Friend",
            "Mahek's Family",
            "Mahek's Wedding Party",
            "Mahek and Saumya's Friend",
        ]

        # Use JavaScript to get the relationship value and events invited to
        try:
            guest_data = page.evaluate('''() => {
                const result = { relationship: '', events_invited: [] };

                // Find relationship value
                const labels = Array.from(document.querySelectorAll('label, span, div')).filter(
                    el => el.textContent.trim() === 'Relationship To You'
                );

                for (const label of labels) {
                    let parent = label.parentElement;
                    if (parent) {
                        const children = parent.querySelectorAll('*');
                        for (const child of children) {
                            const text = child.textContent.trim();
                            if ((text.includes("Mahek") || text.includes("Saumya")) &&
                                !text.includes("Relationship To You") &&
                                !text.includes("Select...") &&
                                text.length < 50) {
                                result.relationship = text;
                                break;
                            }
                        }
                    }
                    if (result.relationship) break;
                }

                // Find events invited to (checked checkboxes)
                const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                for (const cb of checkboxes) {
                    const label = cb.closest('label') || cb.parentElement;
                    const labelText = label ? label.textContent.trim() : '';

                    // Check if this is an event checkbox
                    if (labelText.includes("Vidhi") || labelText.includes("Wedding") || labelText.includes("Reception")) {
                        if (cb.checked) {
                            result.events_invited.push(labelText);
                        }
                    }
                }

                return result;
            }''')

            if guest_data.get('relationship'):
                # Clean up - get just the first relationship value
                rel_value = guest_data['relationship']
                for pattern in relationship_patterns:
                    if pattern in rel_value:
                        info['relationship'] = pattern
                        break
                if not info['relationship'] and rel_value:
                    info['relationship'] = rel_value.split('\n')[0].strip()

            # Store events invited to
            info['events_invited'] = guest_data.get('events_invited', [])

        except Exception as js_err:
            print(f"      JS error: {str(js_err)[:30]}")

    except Exception as e:
        print(f"      Warning extracting guest info: {e}")

    return info


def extract_rsvp_from_modal(page: Page) -> dict:
    """
    Extract RSVP status AND person names from the RSVP Status tab.

    Based on user-provided HTML structure, the RSVP tab has accordion sections:
    <div class="accordion-section selected">
      <h4 role="button"><span>Saumya's Vidhi &amp; Haaldi</span>...</h4>
      <div class="accordion-body">
        <p class="form-control-static">1. Vallabhdas Acharya</p>
        <select name="guests[0].event_invitations[...].rsvp_type" class="form-control">...</select>
        <p class="form-control-static">2. Kishanpyari Acharya</p>
        <select>...</select>
        <p class="form-control-static">3. Harikrishna Acharya</p>
        <select>...</select>
        <p class="form-control-static">4. Vandan Acharya</p>
        <select>...</select>
      </div>
    </div>

    We extract BOTH the names and their RSVP statuses from this tab.
    """
    rsvp_data = {
        'all_statuses': [],
        'events_found': [],
        'people': [],  # List of person names from RSVP tab
        'person_statuses': {},  # {person_name: {event: status}}
    }

    try:
        # Extract names and statuses from accordion sections
        accordion_data = page.evaluate(r'''() => {
            const result = {
                accordion_found: false,
                events: [],
                people: [],
                person_statuses: {},
                all_statuses: []
            };

            // Status value mapping
            const statusMap = {
                'NO_RESPONSE': 'No Response',
                'ATTENDING': 'Attending',
                'DECLINED': 'Declined'
            };

            // Known event names to search for
            const eventNames = [
                "Mahek's Vidhi & Haaldi",
                "Saumya's Vidhi & Haaldi",
                "Wedding",
                "Reception"
            ];

            // Find accordion sections
            const accordionSections = document.querySelectorAll('.accordion-section');
            result.accordion_found = accordionSections.length > 0;

            // Process each accordion section (each event)
            for (const section of accordionSections) {
                // Get event name from h4 span
                const headerSpan = section.querySelector('h4 span');
                if (!headerSpan) continue;

                let eventName = headerSpan.textContent.trim();
                eventName = eventName.replace(/&amp;/g, '&');

                // Match to known event
                const matchedEvent = eventNames.find(e =>
                    eventName.includes(e) || e.includes(eventName) ||
                    eventName.toLowerCase().replace(/[^a-z]/g, '').includes(
                        e.toLowerCase().replace(/[^a-z]/g, '').substring(0, 10)
                    )
                );

                if (!matchedEvent) continue;

                result.events.push(matchedEvent);

                // Get the accordion body with names and selects
                const body = section.querySelector('.accordion-body');
                if (!body) continue;

                // Get all name paragraphs (e.g., "1. Vallabhdas Acharya")
                const nameParagraphs = body.querySelectorAll('p.form-control-static');
                const selects = body.querySelectorAll('select');

                // Extract names and pair with statuses
                for (let i = 0; i < nameParagraphs.length; i++) {
                    let personName = nameParagraphs[i].textContent.trim();
                    // Remove the "1. ", "2. " prefix
                    personName = personName.replace(/^\d+\.\s*/, '');

                    // Add to people list if not already there
                    if (!result.people.includes(personName)) {
                        result.people.push(personName);
                    }

                    // Initialize person's status map if needed
                    if (!result.person_statuses[personName]) {
                        result.person_statuses[personName] = {};
                    }

                    // Get corresponding status
                    if (i < selects.length) {
                        const value = selects[i].value;
                        const status = statusMap[value] || value;
                        result.person_statuses[personName][matchedEvent] = status;
                        result.all_statuses.push(status);
                    }
                }
            }

            return result;
        }''')

        print(f"      Accordion found: {accordion_data.get('accordion_found', False)}")
        print(f"      Events: {accordion_data.get('events', [])}")
        print(f"      People found: {accordion_data.get('people', [])}")
        print(f"      Total statuses: {len(accordion_data.get('all_statuses', []))}")

        rsvp_data['accordion_found'] = accordion_data.get('accordion_found', False)
        rsvp_data['events_found'] = accordion_data.get('events', [])
        rsvp_data['people'] = accordion_data.get('people', [])
        rsvp_data['person_statuses'] = accordion_data.get('person_statuses', {})
        rsvp_data['all_statuses'] = accordion_data.get('all_statuses', [])

    except Exception as e:
        print(f"      Warning extracting RSVP: {e}")

    return rsvp_data


def scrape_guest_from_modal(page: Page, data_dir: Path, guest_num: int) -> dict | None:
    """
    Scrape all data from the currently open guest modal.

    Assumes the modal is already open.
    """
    result = {
        'primary_first': '',
        'primary_last': '',
        'partner_first': '',
        'partner_last': '',
        'relationship': '',
        'rsvp': {},
    }

    try:
        modal = page.locator('dialog, [role="dialog"]').first
        if modal.count() == 0:
            print(f"      No modal found")
            return None

        # === GUEST INFO TAB ===
        # Click Guest Info tab using JavaScript to avoid coordinate issues
        try:
            page.evaluate('''() => {
                const modal = document.querySelector('.modal-content');
                if (!modal) return;
                const tabs = modal.querySelectorAll('nav ul li a, .tabs-label a');
                for (const tab of tabs) {
                    if (tab.textContent.trim() === 'Guest Info') {
                        tab.click();
                        return;
                    }
                }
            }''')
            page.wait_for_timeout(500)
        except:
            pass

        # Extract guest info
        guest_info = extract_guest_info_from_modal(page)
        result.update(guest_info)

        print(f"      Name: {result['primary_first']} {result['primary_last']}")
        if result['partner_first']:
            print(f"      Partner: {result['partner_first']} {result['partner_last']}")
        print(f"      Relationship: {result['relationship']}")

        # === RSVP STATUS TAB ===
        # Use XPath provided by user to click the RSVP Status tab
        # XPath: /html/body/div[1]/div/div/div[2]/div[1]/div/div/div/div[2]/div/div/div/form/div[1]/nav/div/ul/li[3]/a
        rsvp_tab_clicked = False

        # Method 1: Try XPath click via JavaScript
        try:
            rsvp_tab_clicked = page.evaluate('''() => {
                // XPath to RSVP Status tab
                const xpath = "/html/body/div[1]/div/div/div[2]/div[1]/div/div/div/div[2]/div/div/div/form/div[1]/nav/div/ul/li[3]/a";
                const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                const tab = result.singleNodeValue;

                if (tab) {
                    tab.click();
                    return true;
                }
                return false;
            }''')
            if rsvp_tab_clicked:
                page.wait_for_timeout(1000)
                print(f"      Clicked RSVP Status tab via XPath")
        except Exception as xpath_err:
            print(f"      XPath click error: {str(xpath_err)[:30]}")

        # Method 2: Fallback - find by text content
        if not rsvp_tab_clicked:
            try:
                rsvp_tab_clicked = page.evaluate('''() => {
                    const modal = document.querySelector('.modal-content');
                    if (!modal) return false;

                    const tabs = modal.querySelectorAll('nav ul li a, .tabs-label a');
                    for (const tab of tabs) {
                        if (tab.textContent.trim() === 'RSVP Status') {
                            tab.click();
                            return true;
                        }
                    }
                    return false;
                }''')
                if rsvp_tab_clicked:
                    page.wait_for_timeout(1000)
                    print(f"      Clicked RSVP Status tab via text search")
            except Exception as tab_err:
                print(f"      Text search click error: {str(tab_err)[:30]}")

        # === VERIFY WE'RE ON RSVP TAB ===
        # Search for accordion sections with event spans to confirm we're on the right tab
        on_rsvp_tab = page.evaluate('''() => {
            // Look for accordion sections with event names
            const accordionSections = document.querySelectorAll('.accordion-section');
            if (accordionSections.length > 0) return true;

            // Look for h4 buttons with spans containing event names
            const eventHeaders = document.querySelectorAll('h4[role="button"] span');
            for (const span of eventHeaders) {
                const text = span.textContent.toLowerCase();
                if (text.includes('vidhi') || text.includes('haaldi') ||
                    text.includes('wedding') || text.includes('reception')) {
                    return true;
                }
            }

            // Also check for select elements with rsvp_type names
            const rsvpSelects = document.querySelectorAll('select[name*="rsvp_type"]');
            return rsvpSelects.length > 0;
        }''')

        if on_rsvp_tab:
            print(f"      ✓ Verified on RSVP Status tab (accordion/selects found)")
        else:
            print(f"      ⚠ Could not verify RSVP tab - may be on wrong tab")

        # Expand all accordion sections by clicking event buttons
        expanded_count = 0
        if on_rsvp_tab:
            try:
                expanded_count = page.evaluate('''() => {
                    let count = 0;
                    // Click on accordion section headers to expand them
                    const headers = document.querySelectorAll('.accordion-section h4[role="button"]');
                    for (const header of headers) {
                        // Check if section is collapsed (doesn't have 'selected' class on parent)
                        const section = header.closest('.accordion-section');
                        if (section && !section.classList.contains('selected')) {
                            header.click();
                            count++;
                        }
                    }
                    return count;
                }''')
                page.wait_for_timeout(500)
            except Exception as exp_err:
                print(f"      Expand error: {str(exp_err)[:30]}")

            print(f"      Expanded {expanded_count} accordion sections")

        # Extract RSVP data from accordion sections
        rsvp_data = extract_rsvp_from_modal(page)
        result['rsvp'] = rsvp_data

        return result

    except Exception as e:
        print(f"      Error scraping modal: {e}")
        return None


def close_modal(page: Page):
    """Close the modal by clicking X using JavaScript."""
    try:
        # Use JavaScript to click the close button directly
        closed = page.evaluate('''() => {
            // Find the modal close button
            const closeBtn = document.querySelector('.modal-close, .modal-content button.modal-close');
            if (closeBtn) {
                closeBtn.click();
                return true;
            }
            // Fallback: look for × button in modal
            const modal = document.querySelector('.modal-content');
            if (modal) {
                const buttons = modal.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.textContent.trim() === '×') {
                        btn.click();
                        return true;
                    }
                }
            }
            return false;
        }''')

        if closed:
            page.wait_for_timeout(500)
            return
    except:
        pass

    # Fallback: press Escape
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)


def ensure_modal_closed(page: Page):
    """Ensure any open modal is closed before proceeding."""
    try:
        modal = page.locator('dialog, [role="dialog"]')
        if modal.count() > 0:
            close_modal(page)
            page.wait_for_timeout(300)
    except:
        pass


def process_single_guest(
    page: Page,
    data_dir: Path,
    index: int,
    total: int,
    retry_config: RetryConfig,
    attempt: int = 1,
    is_retry_pass: bool = False
) -> tuple[Optional[dict], Optional[FailedGuest]]:
    """
    Process a single guest with retry logic.

    Returns:
        tuple: (result_dict or None, FailedGuest or None)
    """
    guest_num = index + 1

    # Calculate delay based on attempt number
    delay_multiplier = retry_config.retry_delay_multiplier ** (attempt - 1)
    if is_retry_pass:
        click_delay = int(retry_config.slow_mode_delay_ms * delay_multiplier)
        between_delay = int(retry_config.slow_mode_delay_ms * 0.5)
    else:
        click_delay = int(retry_config.base_delay_ms * delay_multiplier)
        between_delay = int(retry_config.base_delay_ms * 0.4)

    # Re-fetch the cells in case DOM changed
    name_cells = page.locator('table tbody tr td:nth-child(2)').all()

    if index >= len(name_cells):
        return None, FailedGuest(index, f"Guest {guest_num}", "Index out of range", attempt)

    cell = name_cells[index]

    # Get the guest name and relationship from the cell
    cell_relationship = ''
    display_name = f"Guest {guest_num}"

    try:
        cell.wait_for(state="visible", timeout=3000)
        cell_text = cell.inner_text(timeout=3000) or ''

        if cell_text:
            lines = [l.strip() for l in cell_text.split('\n') if l.strip()]
            if lines:
                display_name = lines[0][:50]

            for line in lines:
                if line.startswith('(') and line.endswith(')'):
                    cell_relationship = line[1:-1]
                    break
    except Exception as cell_err:
        pass

    attempt_label = f" (attempt {attempt})" if attempt > 1 else ""
    retry_label = " [RETRY PASS]" if is_retry_pass else ""
    print(f"\n[{guest_num}/{total}] {display_name}{attempt_label}{retry_label}")

    try:
        # Find the clickable name element inside the cell
        name_elem = cell.locator('.primary-guest-name').first

        if name_elem.count() == 0:
            name_elem = cell.locator('a, [class*="name"], [class*="guest"]').first

        click_target = name_elem if name_elem.count() > 0 else cell

        # Scroll the element into view first
        click_target.scroll_into_view_if_needed()
        page.wait_for_timeout(200)

        # Click to open modal
        click_target.click(timeout=5000)
        page.wait_for_timeout(click_delay)

        # Verify modal opened
        modal = page.locator('dialog, [role="dialog"]')
        if modal.count() == 0:
            # Try JavaScript click as fallback
            print(f"      Modal did not open, trying JS click...")
            page.wait_for_timeout(300)
            clicked = page.evaluate('''(rowIndex) => {
                const rows = document.querySelectorAll('table tbody tr');
                if (rowIndex >= rows.length) return false;
                const nameCell = rows[rowIndex].querySelector('td:nth-child(2)');
                if (!nameCell) return false;
                const nameElem = nameCell.querySelector('.primary-guest-name') ||
                                 nameCell.querySelector('[class*="name"]') ||
                                 nameCell.querySelector('a');
                if (nameElem) {
                    nameElem.click();
                    return true;
                }
                nameCell.click();
                return true;
            }''', index)
            page.wait_for_timeout(click_delay)
            modal = page.locator('dialog, [role="dialog"]')

        if modal.count() == 0:
            return None, FailedGuest(index, display_name, "Modal did not open", attempt)

        # Scrape data from modal
        result = scrape_guest_from_modal(page, data_dir, guest_num)

        # Close modal
        close_modal(page)
        page.wait_for_timeout(between_delay)

        if result:
            result['row_index'] = index
            result['display_name'] = display_name
            if not result.get('relationship') and cell_relationship:
                result['relationship'] = cell_relationship
            print(f"      ✓ Scraped successfully")
            return result, None
        else:
            return None, FailedGuest(index, display_name, "Failed to extract data from modal", attempt)

    except PlaywrightTimeout:
        ensure_modal_closed(page)
        return None, FailedGuest(index, display_name, "Timeout", attempt)
    except Exception as e:
        ensure_modal_closed(page)
        return None, FailedGuest(index, display_name, f"Error: {str(e)[:50]}", attempt)


def process_guest_with_retries(
    page: Page,
    data_dir: Path,
    index: int,
    total: int,
    retry_config: RetryConfig,
    is_retry_pass: bool = False
) -> tuple[Optional[dict], Optional[FailedGuest]]:
    """
    Process a guest with immediate retries on failure.

    Returns:
        tuple: (result_dict or None, FailedGuest or None if all retries exhausted)
    """
    max_attempts = retry_config.retry_pass_max_attempts if is_retry_pass else retry_config.max_immediate_retries

    for attempt in range(1, max_attempts + 1):
        result, failure = process_single_guest(
            page, data_dir, index, total, retry_config, attempt, is_retry_pass
        )

        if result:
            return result, None

        if failure and attempt < max_attempts:
            print(f"      ✗ {failure.reason} - will retry ({attempt}/{max_attempts})")
            # Ensure modal is closed before retry
            ensure_modal_closed(page)
            # Add increasing delay before retry
            retry_wait = int(retry_config.base_delay_ms * (attempt * 0.5))
            page.wait_for_timeout(retry_wait)
        elif failure:
            failure.attempts = attempt
            print(f"      ✗ {failure.reason} - exhausted retries ({attempt}/{max_attempts})")
            return None, failure

    return None, FailedGuest(index, f"Guest {index + 1}", "Unknown failure", max_attempts)


def get_all_guest_rows(page: Page) -> list[tuple[str, str]]:
    """
    Get all guest rows from the table.

    Returns list of (first_name, last_name) tuples.
    The guest list shows names like "Akshar, Keertan" with relationship below.
    """
    guests = []

    # Find all table rows in the guest list
    rows = page.locator('table tbody tr').all()

    for row in rows:
        try:
            # The first cell contains the name (clickable) and relationship
            first_cell = row.locator('td').first

            # Get the primary name text (first bold/link text)
            # Names appear as "FirstName LastName" or with relationship below
            name_elem = first_cell.locator('a, strong, [class*="name"]').first
            if name_elem.count() == 0:
                # Try getting direct text
                cell_text = first_cell.text_content() or ''
                # Parse "LastName FirstName" or similar
                parts = cell_text.strip().split('\n')[0].split()
                if len(parts) >= 2:
                    guests.append((' '.join(parts[:-1]), parts[-1]))  # Approximate
                continue

            name_text = name_elem.text_content() or ''

            # Also get the relationship text (usually in smaller/gray text below)
            rel_elem = first_cell.locator('[class*="relationship"], [class*="gray"], small')
            relationship = get_text_content(rel_elem) if rel_elem.count() > 0 else ''

            guests.append((name_text.strip(), relationship))

        except Exception as e:
            continue

    return guests


def determine_side(relationship: str) -> str:
    """Determine if a guest is on Bride's or Groom's side based on relationship."""
    rel_lower = relationship.lower()

    if 'saumya' in rel_lower:
        return 'Bride'
    elif 'mahek' in rel_lower:
        return 'Groom'
    else:
        return 'Unknown'


def scroll_to_load_all_guests(page: Page) -> int:
    """Scroll through the guest list to ensure all guests are loaded."""
    last_count = 0
    same_count_iterations = 0

    while same_count_iterations < 3:
        # Count current rows
        rows = page.locator('table tbody tr').all()
        current_count = len(rows)

        if current_count == last_count:
            same_count_iterations += 1
        else:
            same_count_iterations = 0
            last_count = current_count

        # Scroll down
        page.keyboard.press("End")
        page.wait_for_timeout(500)

    # Scroll back to top
    page.keyboard.press("Home")
    page.wait_for_timeout(500)

    return last_count


def save_failed_guests(failed_guests: list[FailedGuest], output_dir: Path, timestamp: str):
    """Save failed guests to a JSON file for debugging."""
    if not failed_guests:
        return

    failed_path = output_dir / f"failed_guests_{timestamp}.json"
    failed_data = {
        'timestamp': timestamp,
        'total_failed': len(failed_guests),
        'guests': [fg.to_dict() for fg in failed_guests],
    }

    with open(failed_path, 'w') as f:
        json.dump(failed_data, f, indent=2)

    print(f"Saved {len(failed_guests)} failed guests to: {failed_path}")


def merge_with_existing_csv(new_results: list[dict], existing_csv_path: Path, output_path: Path):
    """
    Merge new scrape results with an existing CSV.

    New results replace existing rows based on Household_Index.
    Rows not in new results are kept from existing CSV.
    """
    # Load existing CSV
    existing_rows = []
    with open(existing_csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        existing_rows = list(reader)

    print(f"Loaded {len(existing_rows)} rows from existing CSV")

    # Get household indices that were re-scraped
    new_household_indices = set()
    for result in new_results:
        idx = result.get('row_index')
        if idx is not None:
            new_household_indices.add(idx)

    print(f"Re-scraped {len(new_household_indices)} households: {sorted(new_household_indices)}")

    # Filter out old rows for re-scraped households
    kept_rows = [row for row in existing_rows
                 if int(row.get('Household_Index', -1)) not in new_household_indices]

    print(f"Keeping {len(kept_rows)} existing rows (not re-scraped)")

    # Return the kept rows and new results for save_results to handle
    return kept_rows, new_household_indices


def save_results_with_merge(results: list[dict], existing_csv_path: Path, output_path: Path):
    """
    Save scraped results to CSV, merging with existing data.

    Keeps existing rows that weren't re-scraped, replaces rows that were.
    """
    # Get kept rows from existing CSV
    kept_rows, merged_indices = merge_with_existing_csv(results, existing_csv_path, output_path)

    # Process new results into rows
    new_rows = results_to_rows(results)

    # Combine: kept rows + new rows
    all_rows = kept_rows + new_rows

    # Sort by Household_Index to maintain order
    all_rows.sort(key=lambda r: int(r.get('Household_Index', 0)))

    # Write combined CSV
    if all_rows:
        fieldnames = list(all_rows[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"Merged {len(new_rows)} new rows with {len(kept_rows)} existing rows")
        print(f"Saved {len(all_rows)} total individuals to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape guest data from Zola")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of guests to scrape (0 = all)")
    parser.add_argument("--start", type=int, default=0, help="Start from this guest index (0-based)")
    parser.add_argument("--keep-open", type=int, default=5, help="Seconds to keep browser open after completion")
    parser.add_argument("--slow", action="store_true", help="Add extra delays between operations")
    parser.add_argument("--indices", type=str, default="", help="Comma-separated list of specific indices to scrape")
    parser.add_argument("--max-retries", type=int, default=3, help="Max immediate retries per guest")
    parser.add_argument("--no-retry-pass", action="store_true", help="Disable final retry pass for failed guests")
    parser.add_argument("--max-failures", type=int, default=5, help="Max acceptable failures before failing the run")
    parser.add_argument("--from-failed-log", action="store_true", help="Retry guests from the most recent failed_guests JSON")
    parser.add_argument("--merge-with", type=str, default="", help="Path to existing CSV to merge results into")
    args = parser.parse_args()

    # Configure retry behavior
    retry_config = RetryConfig(
        max_immediate_retries=args.max_retries,
        retry_pass_enabled=not args.no_retry_pass,
        max_acceptable_failures=args.max_failures,
        base_delay_ms=1500 if args.slow else 800,
        slow_mode_delay_ms=2500 if args.slow else 2000,
    )

    # Setup directories (need early for --from-failed-log)
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    output_dir = data_dir / "scraped"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse specific indices if provided
    target_indices = None
    if args.indices:
        target_indices = set(int(i.strip()) for i in args.indices.split(',') if i.strip())

    # Load indices from failed guests log if requested
    failed_log_path = None
    if args.from_failed_log:
        # Find the most recent failed_guests_*.json
        failed_logs = sorted(output_dir.glob("failed_guests_*.json"), reverse=True)
        if not failed_logs:
            print("ERROR: No failed_guests_*.json found in data/scraped/")
            print("Run a full scrape first to generate failed guest logs.")
            sys.exit(1)

        failed_log_path = failed_logs[0]
        print(f"Loading failed guests from: {failed_log_path}")

        with open(failed_log_path, 'r') as f:
            failed_data = json.load(f)

        failed_indices = [g['index'] for g in failed_data.get('guests', [])]
        if not failed_indices:
            print("No failed guests found in the log. Nothing to retry!")
            sys.exit(0)

        target_indices = set(failed_indices)
        print(f"Found {len(target_indices)} failed guests to retry: {sorted(target_indices)}")

    # Validate merge-with path if provided
    merge_csv_path = None
    if args.merge_with:
        merge_csv_path = Path(args.merge_with)
        if not merge_csv_path.exists():
            # Try relative to output_dir
            merge_csv_path = output_dir / args.merge_with
            if not merge_csv_path.exists():
                print(f"ERROR: Merge CSV not found: {args.merge_with}")
                sys.exit(1)
        print(f"Will merge results into: {merge_csv_path}")

    # Auto-detect merge CSV when using --from-failed-log
    if args.from_failed_log and not merge_csv_path:
        # Find the most recent non-partial, non-error CSV
        existing_csvs = sorted(
            [f for f in output_dir.glob("zola_guests_*.csv")
             if not any(x in f.name for x in ['partial', 'error', 'interrupted'])],
            reverse=True
        )
        if existing_csvs:
            merge_csv_path = existing_csvs[0]
            print(f"Auto-detected merge target: {merge_csv_path}")

    # Check for session
    session_state = get_session_from_file()
    if not session_state:
        print("ERROR: No saved session found.")
        print("Run: python download_zola_data.py --save-session")
        sys.exit(1)

    # Timestamp for output file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = output_dir / f"zola_guests_{timestamp}.csv"

    print("=" * 60)
    print("ZOLA GUEST DATA SCRAPER")
    print("=" * 60)
    print(f"Output: {output_path}")
    print(f"Headless: {args.headless}")
    if args.limit > 0:
        print(f"Limit: {args.limit} guests")
    if args.start > 0:
        print(f"Starting from guest #{args.start}")

    all_results = []
    failed_guests: list[FailedGuest] = []

    with sync_playwright() as p:
        print("\nLaunching browser...")
        browser = p.chromium.launch(headless=args.headless)

        context = browser.new_context(
            storage_state=session_state,
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        try:
            # Navigate to guest list
            print("\nNavigating to guest list...")
            page.goto(GUEST_LIST_URL)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # Check if logged in
            if "login" in page.url.lower():
                print("ERROR: Session expired. Please run --save-session again.")
                browser.close()
                sys.exit(1)

            print(f"Current URL: {page.url}")
            save_screenshot(page, data_dir, "01_initial")

            # Scroll to load all guests (if paginated/lazy-loaded)
            print("\nLoading all guests...")
            total_rows = scroll_to_load_all_guests(page)
            print(f"Found {total_rows} guest rows")

            # Get all clickable guest name elements
            # Names are in the SECOND column (first column is checkbox)
            # Target the primary-guest-name div which opens the modal when clicked
            name_cells = page.locator('table tbody tr td:nth-child(2)').all()

            print(f"Found {len(name_cells)} guest entries")

            if len(name_cells) == 0:
                print("ERROR: No guests found. Check if the page loaded correctly.")
                save_screenshot(page, data_dir, "error_no_guests")
                browser.close()
                sys.exit(1)

            # Apply limits
            start_idx = args.start
            end_idx = len(name_cells)
            if args.limit > 0:
                end_idx = min(start_idx + args.limit, len(name_cells))

            if target_indices:
                print(f"\nProcessing {len(target_indices)} specific indices: {sorted(target_indices)[:10]}...")
            else:
                print(f"\nProcessing guests {start_idx + 1} to {end_idx}")
            if args.slow:
                print("SLOW MODE: Adding extra delays between operations")
            print(f"Retry config: {retry_config.max_immediate_retries} immediate retries, "
                  f"retry pass {'enabled' if retry_config.retry_pass_enabled else 'disabled'}")
            print("=" * 60)

            # ===== MAIN PASS =====
            for i in range(start_idx, end_idx):
                # Skip if not in target indices (when specified)
                if target_indices and i not in target_indices:
                    continue

                guest_num = i + 1

                result, failure = process_guest_with_retries(
                    page, data_dir, i, end_idx, retry_config, is_retry_pass=False
                )

                if result:
                    all_results.append(result)
                elif failure:
                    failed_guests.append(failure)

                # Progress update every 25 guests
                if guest_num % 25 == 0:
                    print(f"\n{'='*60}")
                    print(f"Progress: {guest_num}/{end_idx} guests "
                          f"({len(all_results)} successful, {len(failed_guests)} failed)")
                    print(f"{'='*60}")

                    # Save intermediate results
                    if all_results:
                        save_results(all_results, output_dir / f"zola_guests_{timestamp}_partial.csv")

            # ===== RETRY PASS =====
            if failed_guests and retry_config.retry_pass_enabled:
                print("\n" + "=" * 60)
                print(f"RETRY PASS: {len(failed_guests)} guests to retry")
                print("=" * 60)

                # Refresh the page before retry pass to ensure clean state
                print("Refreshing page for retry pass...")
                page.reload()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)

                # Scroll to load all guests again
                scroll_to_load_all_guests(page)

                still_failed: list[FailedGuest] = []

                for fg in failed_guests:
                    result, failure = process_guest_with_retries(
                        page, data_dir, fg.index, end_idx, retry_config, is_retry_pass=True
                    )

                    if result:
                        all_results.append(result)
                        print(f"      ✓ Retry successful for {fg.display_name}")
                    elif failure:
                        failure.attempts += fg.attempts  # Add previous attempts
                        still_failed.append(failure)

                failed_guests = still_failed
                print(f"\nRetry pass complete: {len(failed_guests)} guests still failed")

            # Save final results
            print("\n" + "=" * 60)
            print("SCRAPING COMPLETE")
            print("=" * 60)

            total_attempted = end_idx - start_idx
            if target_indices:
                total_attempted = len(target_indices)

            if all_results:
                if merge_csv_path:
                    # Merge with existing CSV
                    save_results_with_merge(all_results, merge_csv_path, output_path)
                else:
                    save_results(all_results, output_path)
                print(f"\nSuccessfully scraped: {len(all_results)}/{total_attempted} guests")
            else:
                print("\nNo results to save!")

            # Save and report failed guests
            if failed_guests:
                save_failed_guests(failed_guests, output_dir, timestamp)
                print(f"\n⚠ FAILED GUESTS ({len(failed_guests)}):")
                for fg in failed_guests:
                    print(f"   [{fg.index + 1}] {fg.display_name}: {fg.reason} (attempts: {fg.attempts})")

            # Keep browser open for inspection
            if not args.headless and args.keep_open > 0:
                print(f"\nBrowser will stay open for {args.keep_open} seconds...")
                time.sleep(args.keep_open)

            # Determine exit code
            if len(failed_guests) > retry_config.max_acceptable_failures:
                print(f"\n❌ FAILURE: {len(failed_guests)} guests failed "
                      f"(max acceptable: {retry_config.max_acceptable_failures})")
                browser.close()
                sys.exit(1)
            elif failed_guests:
                print(f"\n⚠ WARNING: {len(failed_guests)} guests failed, "
                      f"but within acceptable threshold")
            else:
                print(f"\n✓ SUCCESS: All guests scraped successfully")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            if all_results:
                interrupted_path = output_dir / f"zola_guests_{timestamp}_interrupted.csv"
                save_results(all_results, interrupted_path)
            if failed_guests:
                save_failed_guests(failed_guests, output_dir, timestamp)
        except Exception as e:
            print(f"\nERROR: {e}")
            save_screenshot(page, data_dir, "error_screenshot")
            if all_results:
                error_path = output_dir / f"zola_guests_{timestamp}_error.csv"
                save_results(all_results, error_path)
            if failed_guests:
                save_failed_guests(failed_guests, output_dir, timestamp)
            raise
        finally:
            print("\nClosing browser...")
            browser.close()


def results_to_rows(results: list[dict]) -> list[dict]:
    """
    Convert scraped results to CSV rows with one row per person.

    Each person gets their own row. Partners/guests have a 'Guest_Of' column
    linking them to the household head (first person listed).
    """
    rows = []
    for guest in results:
        # Get relationship - try from scraped data first, then from display name
        relationship = guest.get('relationship', '')
        if not relationship:
            display = guest.get('display_name', '')
            if '(' in display and ')' in display:
                start = display.find('(')
                end = display.find(')')
                if start < end:
                    relationship = display[start+1:end].strip()

        side = determine_side(relationship)

        # Get events invited to from guest info
        events_invited = guest.get('events_invited', [])

        # Get RSVP data - now includes people names and their individual statuses
        rsvp = guest.get('rsvp', {})
        people = rsvp.get('people', [])  # Names from RSVP Status tab
        person_statuses = rsvp.get('person_statuses', {})  # {name: {event: status}}

        # If no people found in RSVP tab, fall back to Guest Info textboxes
        if not people:
            primary_first = guest.get('primary_first', '')
            primary_last = guest.get('primary_last', '')
            partner_first = guest.get('partner_first', '')
            partner_last = guest.get('partner_last', '')

            if primary_first or primary_last:
                people.append(f"{primary_first} {primary_last}".strip())
            if partner_first or partner_last:
                people.append(f"{partner_first} {partner_last}".strip())

        if not people:
            # Skip if no people found at all
            continue

        # First person is the head of household
        head_of_household = people[0]

        # Helper to get status for a person and event
        def get_status_for_event(person_name: str, event: str) -> str:
            """Get RSVP status for a specific person and event."""
            if person_name not in person_statuses:
                return ''

            person_events = person_statuses[person_name]

            # Normalize event name for comparison
            event_normalized = event.lower().replace("'", "").replace("&", "and").replace(" ", "")

            for invited_event, status in person_events.items():
                invited_normalized = invited_event.lower().replace("'", "").replace("&", "and").replace(" ", "")
                if event_normalized in invited_normalized or invited_normalized in event_normalized:
                    return status
                # Check key words for Vidhi events
                if "mahek" in event_normalized and "vidhi" in event_normalized:
                    if "mahek" in invited_normalized and "vidhi" in invited_normalized:
                        return status
                if "saumya" in event_normalized and "vidhi" in event_normalized:
                    if "saumya" in invited_normalized and "vidhi" in invited_normalized:
                        return status
            return ''  # Not invited to this event

        # Get household head's name parts for inheritance
        head_name_parts = head_of_household.split()
        head_first_name = head_name_parts[0] if head_name_parts else ''
        head_last_name = ' '.join(head_name_parts[1:]) if len(head_name_parts) > 1 else ''

        # Counter for "Guest" placeholders
        guest_counter = 0

        # Create a row for each person in the household
        for i, person_name in enumerate(people):
            # Keep original name for RSVP lookup (before adding inherited last name)
            original_name = person_name

            # Split name into first and last
            name_parts = person_name.split()
            first_name = name_parts[0] if name_parts else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            # Handle "Guest" placeholder - replace with "HeadFirstName Guest N HeadLastName"
            if first_name == 'Guest' and not last_name:
                guest_counter += 1
                first_name = head_first_name
                last_name = f"Guest {guest_counter} {head_last_name}".strip()
                person_name = f"{first_name} {last_name}"
            # If guest has no last name and is not the head of household,
            # inherit the household head's last name
            elif not last_name and i > 0 and head_last_name:
                if first_name not in ['Child']:
                    last_name = head_last_name
                    person_name = f"{first_name} {last_name}"

            row = {
                'Household_Index': guest.get('row_index', ''),
                'First_Name': first_name,
                'Last_Name': last_name,
                'Full_Name': person_name,
                'Guest_Of': '' if i == 0 else head_of_household,  # First person is head
                'Relationship': relationship,
                'Side': side,
            }

            # Add RSVP columns for each event
            # Use original_name for lookup since that's how it's stored in person_statuses
            for event in EVENTS:
                event_key = event.replace("'", "").replace(" ", "_").replace("&", "and")
                row[f'RSVP_{event_key}'] = get_status_for_event(original_name, event)

            # Add events invited
            row['Events_Invited'] = ', '.join(events_invited) if events_invited else ''

            rows.append(row)

    return rows


def save_results(results: list[dict], output_path: Path):
    """Save scraped results to CSV with one row per person."""
    if not results:
        return

    rows = results_to_rows(results)

    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Saved {len(rows)} individuals to: {output_path}")


if __name__ == "__main__":
    main()
