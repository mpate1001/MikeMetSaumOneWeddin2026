# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wedding planning tools repository for managing RSVPs, website functionality, and related applications for Mike & Saumya's 2026 wedding.

## Purpose

Zola.com lacks robust RSVP tracking and analytics tools. This project:
1. Scrapes/exports RSVP data from the Zola wedding website on a daily basis (automated via GitHub Actions)
2. Stores exported data in `data/scraped/` folder with automatic archival of old files
3. Provides a GitHub Pages-hosted React dashboard to visualize:
   - Who has RSVP'd to each event
   - Which side they're from (bride/groom)
   - Response rates by event and side
   - Contact information for follow-up
   - Countdown timers to wedding day and final count deadline

## Tech Stack

### Backend/Scraper (Python)
- **Playwright** - Browser automation for scraping Zola
- **Pandas** - Data manipulation
- **Phonenumbers** - Phone number formatting
- **Requests** - HTTP client for USPS API

### Frontend/Dashboard (React + TypeScript)
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **TanStack React Table** - Data table component
- **Recharts** - Charts and visualizations
- **PapaParse** - CSV parsing

### CI/CD
- **GitHub Actions** - Automated scraping (daily) and deployment
- **GitHub Pages** - Dashboard hosting

## Architecture

```
├── .github/workflows/     # GitHub Actions automation
│   ├── sync-zola-data.yml # Daily scraper (8 AM UTC)
│   └── deploy-dashboard.yml # Dashboard deployment
├── data/
│   ├── scraped/           # CSV exports (zola_guests_*.csv)
│   │   └── archive/       # Archived old data by month
│   └── screenshots/       # Debug screenshots
├── scripts/               # Python scraper scripts
│   ├── scrape_zola_guests.py  # Main Playwright scraper
│   ├── format_utils.py        # Phone/address formatting
│   ├── archive_old_data.py    # Data retention management
│   └── test_usps.py           # USPS API testing
└── site/                  # React dashboard
    ├── src/
    │   ├── components/    # React components
    │   ├── hooks/         # Custom React hooks
    │   └── types/         # TypeScript types
    ├── public/            # Static assets + data.csv
    └── dist/              # Build output
```

## Development Commands

### Dashboard (React)
```bash
cd site
npm install          # Install dependencies
npm run dev          # Start dev server (http://localhost:5173)
npm run build        # Production build
npm run preview      # Preview production build
```

### Scraper (Python)
```bash
pip install -r requirements.txt
playwright install chromium

# Run scraper
python scripts/scrape_zola_guests.py --headless

# Archive old data files
python scripts/archive_old_data.py --keep 2
```

## Key Events

The wedding has 4 events tracked:
1. Saumya's Vidhi & Haaldi
2. Mahek's Vidhi & Haaldi
3. Wedding (May 24, 2026)
4. Reception

## Color Palette

- `strawberry` (#990000) - Bride's side accent
- `space-indigo` (#2B2D42) - Groom's side accent
- `platinum` (#EDF2F4) - Background
- `crimson` (#D80032) - Declined status

## GitHub Secrets Required

- `ZOLA_SESSION` - Base64-encoded Zola browser session
- `USPS_CONSUMER_KEY` (optional) - USPS API for address validation
- `USPS_CONSUMER_SECRET` (optional) - USPS API credentials
