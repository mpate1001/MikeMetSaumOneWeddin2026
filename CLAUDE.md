# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wedding planning tools repository for managing RSVPs, website functionality, and related applications for a 2026 wedding.

## Purpose

Zola.com lacks robust RSVP tracking and analytics tools. This project:
1. Scrapes/exports RSVP data from the Zola wedding website on a daily basis
2. Stores exported data in `data/` folder in this repo
3. Provides a GitHub-hosted website/dashboard to visualize:
   - Who has RSVP'd
   - Which side they're from (bride/groom)
   - Other RSVP analytics that Zola doesn't provide

## Tech Stack

Python-based project (based on .gitignore configuration).

## Architecture

```
├── data/              # Daily RSVP exports from Zola
├── scraper/           # Scripts to fetch RSVP data from Zola (planned)
└── site/              # Static site for viewing RSVP analytics (planned)
```

## Development Commands

*To be added as the project develops.*
