# Zola RSVP Automation Setup Guide

This guide explains how to set up and maintain the automated Zola RSVP data sync.

## Overview

The automation:
1. Downloads RSVP and Guest List data from Zola daily
2. Merges the data to add "side" (Bride/Groom) information
3. Commits the data to this repository
4. Runs via GitHub Actions on a schedule

## Architecture

```
GitHub Actions (daily at 3 AM EST)
│
├── Step 1: Playwright downloads CSVs
│   ├── data/raw/guest_list_YYYY-MM-DD.csv
│   └── data/raw/rsvps_YYYY-MM-DD.csv
│
├── Step 2: Python script merges data
│   └── data/processed/combined_YYYY-MM-DD.csv
│
└── Step 3: Git commits and pushes changes
```

## Required GitHub Secrets

Go to: **Repository Settings → Secrets and variables → Actions**

| Secret Name | Description |
|-------------|-------------|
| `ZOLA_SESSION` | Base64-encoded browser session (see below) |
| `ZOLA_EMAIL` | Your Zola/Gmail email (backup for re-login) |
| `ZOLA_PASSWORD` | Your Zola password (backup for re-login) |
| `GMAIL_APP_PASSWORD` | Gmail App Password for OTP (backup) |

## Session-Based Authentication

Zola has bot detection that blocks automated logins from cloud servers. To bypass this, we use **persistent sessions**:

1. You login once on your local machine
2. The browser session (cookies) is saved
3. GitHub Actions reuses that session - no login needed

### Creating a New Session

**When to do this:**
- First time setup
- When the session expires (you'll see "Session expired" errors)

**Steps:**

```bash
# 1. Set credentials
export ZOLA_EMAIL='your-email@gmail.com'
export ZOLA_PASSWORD='your-zola-password'
export GMAIL_APP_PASSWORD='your-16-char-app-password'

# 2. Run with visible browser
export HEADLESS=false

# 3. Create and save session
python scripts/download_zola_data.py --save-session
```

This will:
- Open a browser window
- Login to Zola (enter OTP if prompted)
- Save session to `data/.zola_session.json.b64`

**Then add to GitHub:**
1. Open `data/.zola_session.json.b64`
2. Copy the entire content
3. Go to GitHub → Settings → Secrets → Actions
4. Create/update secret named `ZOLA_SESSION` with the content

## Gmail App Password Setup

Required for automatic OTP fetching during login.

### Step 1: Enable 2-Step Verification
1. Go to: https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Follow the setup prompts

### Step 2: Create App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select app: "Other (Custom name)"
3. Enter name: `Zola RSVP Automation`
4. Click "Generate"
5. Copy the 16-character password (remove spaces)

## Running Locally

### Download Data Only
```bash
python scripts/download_zola_data.py
```

### Parse/Merge Data Only
```bash
python scripts/parse_rsvps.py --date YYYY-MM-DD
```

### Full Flow with Visible Browser
```bash
export HEADLESS=false
python scripts/download_zola_data.py
python scripts/parse_rsvps.py
```

## Troubleshooting

### "Session expired" Error
Re-create the session:
```bash
export HEADLESS=false
python scripts/download_zola_data.py --save-session
```
Then update the `ZOLA_SESSION` secret on GitHub.

### "Login failed" Error on GitHub Actions
This usually means:
1. Session expired → Re-create session locally
2. Zola changed their site → Check for script updates

### Downloads Work Locally but Fail on GitHub
The session might be tied to your local IP. Try:
1. Re-create session with a fresh login
2. Make sure OTP was completed during session creation

### OTP Not Being Fetched
1. Verify `GMAIL_APP_PASSWORD` is correct (16 chars, no spaces)
2. Make sure IMAP is enabled in Gmail settings
3. Check that Zola emails aren't going to spam

## File Structure

```
MikeMetSaumOneWeddin2026/
├── .github/workflows/
│   └── sync-zola-data.yml     # GitHub Actions workflow
├── data/
│   ├── raw/                    # Downloaded CSVs (timestamped)
│   ├── processed/              # Merged CSVs (timestamped)
│   ├── .zola_session.json      # Local session (gitignored)
│   └── .zola_session.json.b64  # Base64 for GitHub (gitignored)
├── scripts/
│   ├── download_zola_data.py   # Playwright automation
│   └── parse_rsvps.py          # Data merging script
├── docs/
│   └── AUTOMATION_SETUP.md     # This file
└── requirements.txt
```

## Workflow Schedule

The GitHub Action runs:
- **Daily at 8:00 UTC (3:00 AM EST)**
- **On push to main** (when scripts change)
- **Manually** via "Run workflow" button

To change the schedule, edit `.github/workflows/sync-zola-data.yml`:
```yaml
schedule:
  - cron: '0 8 * * *'  # 8 AM UTC = 3 AM EST
```

## Data Output

### Combined CSV Columns
| Column | Description |
|--------|-------------|
| Title, First Name, Last Name, Suffix | Guest identity |
| Saumya's Vidhi & Haaldi | RSVP status |
| Mahek's Vidhi & Haaldi | RSVP status |
| Wedding | RSVP status |
| Reception | RSVP status |
| Side | Relationship (e.g., "Saumya's Family Friend") |
| Bride_or_Groom | Simplified: "Bride" or "Groom" |

### RSVP Status Values
- `Attending` - Confirmed yes
- `Declined` - Confirmed no
- `No Response` - Haven't responded yet
- `Not Invited` - Not invited to that event
