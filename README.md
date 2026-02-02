# MikeMetSaumOneWeddin2026

Wedding planning tools for managing RSVPs and analytics for the 2026 wedding.

## Problem

Zola.com lacks robust RSVP tracking and analytics tools. Their CSV export ignores filters and doesn't include relationship data alongside RSVP status.

## Solution

This project:
1. **Scrapes** RSVP data directly from Zola (daily via GitHub Actions)
2. **Stores** exported data in `data/scraped/` folder
3. **Displays** a dashboard with RSVP analytics that Zola doesn't provide

## Architecture

```
├── .github/workflows/
│   ├── sync-zola-data.yml      # Daily scraper (8 AM UTC)
│   └── deploy-dashboard.yml    # Deploys dashboard to GitHub Pages
├── data/
│   ├── scraped/                # Scraped CSV files (zola_guests_*.csv)
│   └── .zola_session.json      # Zola login session (not committed)
├── scripts/
│   └── scrape_zola_guests.py   # Main scraper script
└── site/                       # React dashboard
    ├── src/
    │   ├── components/         # React components
    │   ├── hooks/              # useGuestData hook
    │   └── types/              # TypeScript types
    └── public/
        └── data.csv            # Latest data for dashboard
```

## Scraper (`scripts/scrape_zola_guests.py`)

Playwright-based scraper that:
- Opens each guest's modal on Zola
- Extracts Guest Info (names, relationship) and RSVP Status (per event)
- Outputs one row per person (not per household)
- Handles "Guest" placeholders by renaming to "FirstName Guest N LastName"

### Multi-Layer Retry Strategy

The scraper has robust retry logic to handle flaky modal opens:

1. **Immediate Retry**: Each guest gets 3 attempts with increasing delays
2. **Retry Pass**: After main scrape, refreshes page and retries all failures
3. **Failed Guest Log**: Saves `failed_guests_*.json` for debugging
4. **Exit Codes**: Fails if more than 5 guests can't be scraped

### CLI Options

```bash
python scripts/scrape_zola_guests.py --help

Options:
  --headless          Run browser in headless mode
  --limit N           Limit to first N guests (for testing)
  --start N           Start from guest index N
  --slow              Add extra delays between operations
  --max-retries N     Immediate retries per guest (default: 3)
  --no-retry-pass     Disable final retry pass
  --max-failures N    Acceptable failures before failing (default: 5)
  --keep-open N       Seconds to keep browser open after (default: 5)
  --from-failed-log   Retry only guests from most recent failed_guests JSON
  --merge-with PATH   Merge results into existing CSV (auto-detected with --from-failed-log)
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Save Zola session (one-time, requires manual login)
python scripts/scrape_zola_guests.py --save-session

# Run scraper
python scripts/scrape_zola_guests.py

# Run in headless mode
python scripts/scrape_zola_guests.py --headless

# Test with first 10 guests
python scripts/scrape_zola_guests.py --limit 10
```

## Dashboard (`site/`)

React + TypeScript + Tailwind CSS dashboard showing:
- **Summary Cards**: Total guests, response rate, per-event stats
- **Pie Charts**: Bride vs Groom split per event
- **Guest Table**: Searchable/filterable guest list
- **Filters**: By side (Bride/Groom), RSVP status, relationship

### Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| Space Indigo | `#2B2D42` | Primary dark (headers, accents) |
| Lavender Grey | `#8D99AE` | Secondary (muted text) |
| Platinum | `#EDF2F4` | Background (light surfaces) |
| Strawberry | `#EF233C` | Accent (vibrant red) |
| Crimson | `#D80032` | Declined/negative states |

### Running Locally

```bash
cd site
npm install
npm run dev
# Opens at http://localhost:5173/MikeMetSaumOneWeddin2026/
```

### Building

```bash
cd site
npm run build
# Output in site/dist/
```

## GitHub Actions

### Sync Zola RSVP Data (`.github/workflows/sync-zola-data.yml`)

- **Schedule**: Daily at 8 AM UTC (3 AM EST / 12 AM PST)
- **Manual**: Can trigger from Actions tab with run mode selection

#### Run Modes

| Mode | Description |
|------|-------------|
| `full` (default) | Scrapes all guests (~30 min). Used for scheduled daily runs. |
| `retry-failed` | Only re-scrapes guests from the most recent `failed_guests_*.json`, merges into existing CSV. Fast! |

#### Workflow Steps

1. Restores Zola session from GitHub Secrets
2. Runs scraper (full or retry-failed based on mode)
3. Copies latest CSV to `site/public/data.csv`
4. Commits and pushes if changes detected
5. **If failures**: Creates/updates a GitHub Issue with failed guest details
6. **If retry succeeds**: Auto-closes the failure issue

#### Failure Notifications

When guests fail to scrape, the workflow:
1. Creates a GitHub Issue labeled `scraper-alert`
2. Lists which guests failed and why
3. Provides instructions to run `retry-failed` mode

You'll get an email notification (if enabled in GitHub) when an issue is created.

### Deploy Dashboard (`.github/workflows/deploy-dashboard.yml`)

- **Triggers**: After sync completes, on push to `site/**`, or manually
- **Steps**:
  1. Copies latest `data/scraped/zola_guests_*.csv` to `site/public/data.csv`
  2. Builds React app
  3. Deploys to GitHub Pages

## CSV Format

Output CSV has one row per person:

| Column | Description |
|--------|-------------|
| `Household_Index` | Row index in Zola guest list |
| `First_Name` | Person's first name |
| `Last_Name` | Person's last name |
| `Full_Name` | Combined name |
| `Guest_Of` | Head of household (empty if this is the head) |
| `Relationship` | Relationship type (e.g., "Saumya's Family") |
| `Side` | Bride or Groom |
| `Email` | Household email (empty if none) |
| `Phone` | Household phone/mobile (empty if none) |
| `Address` | Household mailing address (empty if none) |
| `RSVP_Maheks_Vidhi_and_Haaldi` | RSVP status for event |
| `RSVP_Saumyas_Vidhi_and_Haaldi` | RSVP status for event |
| `RSVP_Wedding` | RSVP status for event |
| `RSVP_Reception` | RSVP status for event |

RSVP Status values: `Attending`, `Declined`, `No Response`, or empty (not invited)

## Secrets Required

In GitHub repository settings, add:

- `ZOLA_SESSION`: Base64-encoded Zola session JSON
  ```bash
  # Generate with:
  cat data/.zola_session.json | base64
  ```

## Troubleshooting

### Scraper failures
- Check `failed_guests_*.json` in `data/scraped/` for details
- Try running with `--slow` flag for more reliable (but slower) scraping
- Check if Zola session has expired

### Dashboard shows wrong count
- Verify `site/public/data.csv` has the latest data
- Check that `useGuestData.ts` parses the CSV format correctly
- Clear browser cache

### GitHub Actions failing
- Check Actions tab for error logs
- Verify `ZOLA_SESSION` secret is set and not expired
- Manual trigger to test: Actions > workflow > "Run workflow"
