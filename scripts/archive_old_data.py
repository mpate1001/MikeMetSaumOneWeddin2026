#!/usr/bin/env python3
"""
Archive old scraped data files to keep the repo clean.

Keeps the most recent complete CSV file in data/scraped/ and moves
older files to data/scraped/archive/ organized by year-month.
"""

import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import re


def get_file_date(filename: str) -> datetime | None:
    """Extract date from filename like zola_guests_2026-02-02_17-47-29.csv"""
    match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})', filename)
    if match:
        date_str = f"{match.group(1)}_{match.group(2)}"
        return datetime.strptime(date_str, '%Y-%m-%d_%H-%M-%S')
    return None


def archive_old_files(
    scraped_dir: Path,
    keep_recent: int = 1,
    dry_run: bool = False
) -> dict:
    """
    Archive old scraped files, keeping the most recent ones.

    Args:
        scraped_dir: Path to the data/scraped directory
        keep_recent: Number of recent complete files to keep (default: 1)
        dry_run: If True, only print what would be done

    Returns:
        Dict with counts of archived, kept, and skipped files
    """
    archive_dir = scraped_dir / 'archive'

    # Get all CSV files (excluding archive directory)
    csv_files = []
    for f in scraped_dir.glob('*.csv'):
        if f.is_file():
            csv_files.append(f)

    # Get all JSON files (failed_guests logs)
    json_files = list(scraped_dir.glob('*.json'))

    # Separate complete and partial files
    complete_files = [f for f in csv_files if '_partial' not in f.name]
    partial_files = [f for f in csv_files if '_partial' in f.name]

    # Sort by date (newest first)
    complete_files.sort(key=lambda f: get_file_date(f.name) or datetime.min, reverse=True)
    partial_files.sort(key=lambda f: get_file_date(f.name) or datetime.min, reverse=True)
    json_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    results = {
        'archived': [],
        'kept': [],
        'skipped': [],
        'errors': []
    }

    # Keep the most recent complete files
    files_to_keep = set()
    for f in complete_files[:keep_recent]:
        files_to_keep.add(f)
        results['kept'].append(f.name)

        # Also keep the corresponding partial file if it exists
        partial_name = f.name.replace('.csv', '_partial.csv')
        partial_path = scraped_dir / partial_name
        if partial_path.exists():
            files_to_keep.add(partial_path)
            results['kept'].append(partial_name)

    # Archive older complete files and their partials
    files_to_archive = []
    for f in complete_files[keep_recent:]:
        files_to_archive.append(f)
        # Find corresponding partial
        partial_name = f.name.replace('.csv', '_partial.csv')
        partial_path = scraped_dir / partial_name
        if partial_path.exists():
            files_to_archive.append(partial_path)

    # Archive orphaned partial files (no corresponding complete file)
    for f in partial_files:
        if f not in files_to_keep and f not in files_to_archive:
            files_to_archive.append(f)

    # Archive old JSON logs (keep only the most recent)
    for f in json_files[1:]:
        files_to_archive.append(f)
    if json_files:
        results['kept'].append(json_files[0].name)

    # Perform archiving
    for f in files_to_archive:
        file_date = get_file_date(f.name)
        if file_date:
            # Organize by year-month
            month_dir = archive_dir / file_date.strftime('%Y-%m')
        else:
            # Fallback for files without parseable dates
            month_dir = archive_dir / 'misc'

        dest = month_dir / f.name

        if dry_run:
            print(f"Would archive: {f.name} -> {dest.relative_to(scraped_dir)}")
            results['archived'].append(f.name)
        else:
            try:
                month_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), str(dest))
                results['archived'].append(f.name)
                print(f"Archived: {f.name} -> {dest.relative_to(scraped_dir)}")
            except Exception as e:
                results['errors'].append((f.name, str(e)))
                print(f"Error archiving {f.name}: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Archive old scraped data files to keep the repo clean.'
    )
    parser.add_argument(
        '--keep', '-k',
        type=int,
        default=1,
        help='Number of recent complete files to keep (default: 1)'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without actually moving files'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default=None,
        help='Path to data directory (default: auto-detect from script location)'
    )

    args = parser.parse_args()

    # Find the data/scraped directory
    if args.data_dir:
        scraped_dir = Path(args.data_dir) / 'scraped'
    else:
        # Auto-detect based on script location
        script_dir = Path(__file__).parent
        scraped_dir = script_dir.parent / 'data' / 'scraped'

    if not scraped_dir.exists():
        print(f"Error: Scraped directory not found: {scraped_dir}")
        return 1

    print(f"Scraped directory: {scraped_dir}")
    print(f"Keeping {args.keep} most recent complete file(s)")
    if args.dry_run:
        print("DRY RUN - no files will be moved\n")
    print()

    results = archive_old_files(
        scraped_dir=scraped_dir,
        keep_recent=args.keep,
        dry_run=args.dry_run
    )

    print()
    print("=" * 50)
    print(f"Kept: {len(results['kept'])} files")
    print(f"Archived: {len(results['archived'])} files")
    if results['errors']:
        print(f"Errors: {len(results['errors'])} files")
        for name, error in results['errors']:
            print(f"  - {name}: {error}")

    return 0


if __name__ == '__main__':
    exit(main())
