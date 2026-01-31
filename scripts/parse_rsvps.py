#!/usr/bin/env python3
"""
RSVP Data Parser

Merges RSVP data with Guest List data to add "side" (Relationship To Couple)
information to each individual guest.

Usage:
    python parse_rsvps.py                           # Auto-finds most recent files
    python parse_rsvps.py --date 2026-01-31         # Uses specific date (legacy format)
    python parse_rsvps.py --date 2026-01-31_14-30-00  # Uses specific timestamp
"""

import pandas as pd
import argparse
import re
from datetime import datetime
from pathlib import Path


def find_most_recent_files(data_dir: Path) -> tuple[Path, Path, str]:
    """
    Find the most recent RSVP and Guest List files in the raw directory.

    Returns:
        tuple: (rsvps_path, guest_list_path, timestamp_str)
    """
    raw_dir = data_dir / "raw"

    # Find all RSVP files
    rsvp_files = list(raw_dir.glob("rsvps_*.csv"))
    if not rsvp_files:
        raise FileNotFoundError(f"No RSVP files found in {raw_dir}")

    # Sort by modification time (most recent first)
    rsvp_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    most_recent_rsvp = rsvp_files[0]

    # Extract timestamp from filename (supports both YYYY-MM-DD and YYYY-MM-DD_HH-MM-SS)
    # Pattern: rsvps_YYYY-MM-DD.csv or rsvps_YYYY-MM-DD_HH-MM-SS.csv
    match = re.search(r'rsvps_(\d{4}-\d{2}-\d{2}(?:_\d{2}-\d{2}-\d{2})?)', most_recent_rsvp.name)
    if not match:
        raise ValueError(f"Could not parse timestamp from filename: {most_recent_rsvp.name}")

    timestamp_str = match.group(1)

    # Find matching guest list file
    guest_list_path = raw_dir / f"guest_list_{timestamp_str}.csv"
    if not guest_list_path.exists():
        # Try to find a guest list file with the same date prefix
        date_prefix = timestamp_str.split('_')[0]
        guest_list_candidates = list(raw_dir.glob(f"guest_list_{date_prefix}*.csv"))
        if guest_list_candidates:
            guest_list_candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            guest_list_path = guest_list_candidates[0]
        else:
            raise FileNotFoundError(f"Guest list file not found for timestamp: {timestamp_str}")

    print(f"Auto-detected most recent files:")
    print(f"  RSVP: {most_recent_rsvp.name}")
    print(f"  Guest List: {guest_list_path.name}")

    return most_recent_rsvp, guest_list_path, timestamp_str


def load_data(data_dir: Path, date_str: str = None) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """
    Load RSVP and Guest List CSVs.

    If date_str is None, automatically finds the most recent files.
    Returns the timestamp string used (for output file naming).
    """
    if date_str is None:
        rsvps_path, guest_list_path, timestamp_str = find_most_recent_files(data_dir)
    else:
        rsvps_path = data_dir / "raw" / f"rsvps_{date_str}.csv"
        guest_list_path = data_dir / "raw" / f"guest_list_{date_str}.csv"
        timestamp_str = date_str

        if not rsvps_path.exists():
            raise FileNotFoundError(f"RSVP file not found: {rsvps_path}")
        if not guest_list_path.exists():
            raise FileNotFoundError(f"Guest list file not found: {guest_list_path}")

    rsvps_df = pd.read_csv(rsvps_path)
    guest_list_df = pd.read_csv(guest_list_path)

    print(f"Loaded {len(rsvps_df)} individuals from RSVPs")
    print(f"Loaded {len(guest_list_df)} households from Guest List")

    return rsvps_df, guest_list_df, timestamp_str


def normalize_name(first: str, last: str) -> str:
    """Normalize a name for matching (lowercase, stripped)."""
    first = str(first).strip().lower() if pd.notna(first) else ""
    last = str(last).strip().lower() if pd.notna(last) else ""
    return f"{first}|{last}"


def build_name_to_side_map(guest_list_df: pd.DataFrame) -> dict[str, str]:
    """
    Build a mapping from normalized name to "Relationship To Couple" (side).

    Includes: primary person, partner, and all children (1-5).
    """
    name_to_side = {}

    for _, row in guest_list_df.iterrows():
        side = row.get("Relationship To Couple", "")
        if pd.isna(side) or side == "":
            continue

        # Primary person
        primary_name = normalize_name(row.get("First Name"), row.get("Last Name"))
        if primary_name != "|":
            name_to_side[primary_name] = side

        # Partner
        partner_name = normalize_name(row.get("Partner First Name"), row.get("Partner Last Name"))
        if partner_name != "|":
            name_to_side[partner_name] = side

        # Children 1-5
        for i in range(1, 6):
            child_first = row.get(f"Child {i} First Name")
            child_last = row.get(f"Child {i} Last Name")
            child_name = normalize_name(child_first, child_last)
            if child_name != "|":
                name_to_side[child_name] = side

    print(f"Built name-to-side mapping with {len(name_to_side)} entries")
    return name_to_side


def merge_data(rsvps_df: pd.DataFrame, name_to_side: dict[str, str]) -> pd.DataFrame:
    """Add 'Side' column to RSVP data by matching names."""

    def get_side(row):
        name = normalize_name(row.get("First Name"), row.get("Last Name"))
        return name_to_side.get(name, "Unknown")

    rsvps_df = rsvps_df.copy()
    rsvps_df["Side"] = rsvps_df.apply(get_side, axis=1)

    # Count matches
    matched = (rsvps_df["Side"] != "Unknown").sum()
    unmatched = (rsvps_df["Side"] == "Unknown").sum()
    print(f"Matched: {matched}, Unmatched: {unmatched}")

    if unmatched > 0:
        print("\nUnmatched names (first 10):")
        unmatched_df = rsvps_df[rsvps_df["Side"] == "Unknown"]
        for _, row in unmatched_df.head(10).iterrows():
            print(f"  - {row.get('First Name', '')} {row.get('Last Name', '')}")

    return rsvps_df


def categorize_side(side: str) -> str:
    """Categorize side into Bride (Saumya) or Groom (Mahek)."""
    if pd.isna(side) or side == "" or side == "Unknown":
        return "Unknown"
    side_lower = side.lower()
    if "saumya" in side_lower:
        return "Bride"
    elif "mahek" in side_lower:
        return "Groom"
    return "Unknown"


def add_summary_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add summary columns for easier analysis."""
    df = df.copy()

    # Add Bride/Groom category
    df["Bride_or_Groom"] = df["Side"].apply(categorize_side)

    # Standardize RSVP values for easier filtering
    event_columns = [
        "Saumya's Vidhi & Haaldi",
        "Mahek's Vidhi & Haaldi",
        "Wedding",
        "Reception"
    ]

    for col in event_columns:
        if col in df.columns:
            df[col] = df[col].fillna("Not Invited")
            df[col] = df[col].replace("", "Not Invited")

    return df


def save_output(df: pd.DataFrame, data_dir: Path, date_str: str) -> Path:
    """Save the merged data to processed folder."""
    output_path = data_dir / "processed" / f"combined_{date_str}.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved combined data to: {output_path}")
    return output_path


def print_summary(df: pd.DataFrame):
    """Print summary statistics."""
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)

    print(f"\nTotal Guests: {len(df)}")

    # By side
    print("\nBy Side (Bride/Groom):")
    print(df["Bride_or_Groom"].value_counts().to_string())

    print("\nBy Relationship:")
    print(df["Side"].value_counts().to_string())

    # By RSVP status for Wedding
    if "Wedding" in df.columns:
        print("\nWedding RSVP Status:")
        print(df["Wedding"].value_counts().to_string())

    # By RSVP status for Reception
    if "Reception" in df.columns:
        print("\nReception RSVP Status:")
        print(df["Reception"].value_counts().to_string())


def main():
    parser = argparse.ArgumentParser(description="Parse and merge RSVP data")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Timestamp of data files (YYYY-MM-DD or YYYY-MM-DD_HH-MM-SS). "
             "If not specified, automatically uses the most recent files."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to data directory"
    )
    args = parser.parse_args()

    # Determine data directory
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        # Default: assume script is in scripts/, data is in ../data/
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data"

    print(f"Data directory: {data_dir}")
    if args.date:
        print(f"Using specified timestamp: {args.date}")
    else:
        print("Auto-detecting most recent files...")
    print()

    # Load data (returns timestamp_str for output file naming)
    rsvps_df, guest_list_df, timestamp_str = load_data(data_dir, args.date)

    # Build name-to-side mapping
    name_to_side = build_name_to_side_map(guest_list_df)

    # Merge data
    merged_df = merge_data(rsvps_df, name_to_side)

    # Add summary columns
    merged_df = add_summary_columns(merged_df)

    # Save output with the same timestamp as input files
    save_output(merged_df, data_dir, timestamp_str)

    # Print summary
    print_summary(merged_df)


if __name__ == "__main__":
    main()
