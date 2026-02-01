# RSVP Dashboard Design

## Overview

A GitHub Pages-hosted dashboard to visualize and track wedding RSVPs, replacing Zola's limited analytics.

## Requirements

- Visual dashboard with charts prominently displayed
- Searchable, filterable guest table with power user features
- Global filters that affect all metrics and charts
- Public access (no authentication)
- Auto-updates when new RSVP data is synced

## Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Deep Burgundy | #780000 | Bride's side in charts |
| Crimson | #C1121F | Accents, buttons, highlights |
| Cream | #FDF0D5 | Background |
| Navy | #003049 | Headers, text, primary UI |
| Steel Blue | #669BBC | Groom's side in charts |

## Page Layout

### Header
- Wedding title: "Saumya & Mahek's Wedding - RSVP Dashboard"
- Last updated timestamp from data file

### Global Filter Bar
- **Side toggle**: All / Bride / Groom
- **RSVP Status pills**: All / Attending / Declined / No Response
- **Relationship dropdown**: All / Family / Friends / Family Friends
- **Clear Filters button**
- Shows "Showing X of Y guests" context

All filters use AND logic and affect every component on the page.

### Summary Cards Row
Four cards showing (filtered) counts:
1. Response Rate (% with progress ring)
2. Wedding headcount
3. Reception headcount
4. Vidhi & Haaldi headcount

### Charts Section

**Row 1 (two columns):**
- Bride vs Groom pie chart
- Response rate progress bars

**Row 2:**
- Attendance by Event: Horizontal stacked bar chart
- Shows Attending/Declined/No Response per event (all 4 events)

**Row 3:**
- Breakdown by Relationship: Bar chart
- Family vs Friends vs Family Friends

### Guest Table

**Features:**
- Search by name (instant filter)
- Export CSV button (exports current filtered view)
- Group by dropdown: None / Side / Relationship / RSVP Status
- Sortable columns (click header)
- Checkbox selection with bulk select/clear
- Visual RSVP icons: ✅ Attending, ❌ Declined, ⏳ No Response
- Pagination (50 per page)

**Columns:**
- Checkbox
- Name (First + Last)
- Side (Bride/Groom)
- Wedding RSVP
- Reception RSVP
- Relationship

## Technical Architecture

### Tech Stack
- React 18 + TypeScript
- Tailwind CSS (custom theme with wedding colors)
- Recharts (charts)
- TanStack Table (table with sorting/filtering/grouping)
- PapaParse (CSV parsing)
- Vite (build tool)

### File Structure
```
MikeMetSaumOneWeddin2026/
├── data/
│   └── processed/combined_*.csv
├── site/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   ├── SummaryCards.tsx
│   │   │   ├── Charts.tsx
│   │   │   └── GuestTable.tsx
│   │   ├── hooks/
│   │   │   └── useGuestData.ts
│   │   └── types/
│   │       └── guest.ts
│   ├── public/
│   │   └── data.csv
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── .github/workflows/
│   ├── sync-zola-data.yml (existing)
│   └── deploy-dashboard.yml (new)
└── scripts/ (existing)
```

### Deployment Flow
1. GitHub Actions syncs Zola data daily (existing workflow)
2. New workflow triggers after data sync
3. Copies latest `combined_*.csv` to `site/public/data.csv`
4. Builds React app with Vite
5. Deploys to `gh-pages` branch
6. Site available at: `https://mpate1001.github.io/MikeMetSaumOneWeddin2026/`

### Data Flow
1. Browser loads `data.csv` via fetch
2. PapaParse parses CSV to JSON
3. React state holds all guests + active filters
4. Filtered data computed via useMemo
5. All components receive filtered data

## RSVP Status Values
- `Attending` - Confirmed yes
- `Declined` - Confirmed no
- `No Response` - Haven't responded yet
- `Not Invited` - Not invited to that specific event

## Events
1. Saumya's Vidhi & Haaldi
2. Mahek's Vidhi & Haaldi
3. Wedding
4. Reception
