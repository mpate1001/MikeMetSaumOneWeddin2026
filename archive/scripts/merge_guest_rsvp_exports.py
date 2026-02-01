#!/usr/bin/env python3
"""
Merge Guest List and RSVP exports from Zola.

This script merges two Zola exports:
1. Guest List export - contains Relationship To Couple (but not RSVP status)
2. RSVP export - contains RSVP status (but not Relationship)

The merge adds the Relationship field to the RSVP data, which allows us to:
- Distinguish guests with the same name on different sides
- Tag each guest as Bride or Groom side

Usage:
    python merge_guest_rsvp_exports.py --guest-list export.csv --rsvps rsvps.csv
    python merge_guest_rsvp_exports.py  # Auto-detect files in Downloads
"""

import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path


def find_latest_exports(downloads_dir: Path) -> tuple[Path | None, Path | None]:
    """Find the most recent guest list and RSVP exports in Downloads."""
    csv_files = sorted(downloads_dir.glob("export*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)

    guest_list_file = None
    rsvp_file = None

    for f in csv_files:
        # Read first line to check columns
        with open(f, 'r') as fp:
            header = fp.readline()

        if 'Relationship To Couple' in header and guest_list_file is None:
            guest_list_file = f
            print(f"Found Guest List export: {f.name}")
        elif "Vidhi & Haaldi" in header and rsvp_file is None:
            rsvp_file = f
            print(f"Found RSVP export: {f.name}")

        if guest_list_file and rsvp_file:
            break

    return guest_list_file, rsvp_file


def build_name_to_relationship_map(guest_list_df: pd.DataFrame) -> dict[str, str]:
    """
    Build a mapping from (First Name, Last Name) -> Relationship.

    The Guest List export contains households with:
    - Primary guest: First Name, Last Name
    - Partner: Partner First Name, Partner Last Name
    - Children: Child 1-5 First Name, Child 1-5 Last Name

    All members of a household share the same Relationship.
    """
    name_to_rel = {}

    for _, row in guest_list_df.iterrows():
        relationship = str(row.get('Relationship To Couple', '')).strip()
        if not relationship:
            continue

        # Primary guest
        first = str(row.get('First Name', '')).strip()
        last = str(row.get('Last Name', '')).strip()
        if first:
            key = (first.lower(), last.lower())
            name_to_rel[key] = relationship

        # Partner
        partner_first = str(row.get('Partner First Name', '')).strip()
        partner_last = str(row.get('Partner Last Name', '')).strip()
        if partner_first:
            # Partner might have different last name or same
            p_last = partner_last if partner_last else last
            key = (partner_first.lower(), p_last.lower())
            name_to_rel[key] = relationship

        # Children (up to 5)
        for i in range(1, 6):
            child_first = str(row.get(f'Child {i} First Name', '')).strip()
            child_last = str(row.get(f'Child {i} Last Name', '')).strip()
            if child_first:
                c_last = child_last if child_last else last
                key = (child_first.lower(), c_last.lower())
                name_to_rel[key] = relationship

    return name_to_rel


def determine_side(relationship: str) -> str:
    """Determine if a guest is on Bride's or Groom's side based on relationship."""
    rel_lower = relationship.lower()

    if 'saumya' in rel_lower:
        return 'Bride'
    elif 'mahek' in rel_lower:
        return 'Groom'
    else:
        return 'Unknown'


def merge_exports(guest_list_path: Path, rsvp_path: Path, output_path: Path):
    """Merge guest list and RSVP exports."""
    print(f"\nLoading Guest List export: {guest_list_path}")
    guest_df = pd.read_csv(guest_list_path)
    print(f"  - {len(guest_df)} households")

    print(f"\nLoading RSVP export: {rsvp_path}")
    rsvp_df = pd.read_csv(rsvp_path)
    print(f"  - {len(rsvp_df)} individuals")

    # Build name -> relationship mapping
    print("\nBuilding name-to-relationship mapping...")
    name_to_rel = build_name_to_relationship_map(guest_df)
    print(f"  - {len(name_to_rel)} name mappings created")

    # Add Relationship and Side columns to RSVP data
    print("\nMerging relationship data into RSVP export...")

    relationships = []
    sides = []
    matched = 0
    unmatched = 0

    for _, row in rsvp_df.iterrows():
        first = str(row.get('First Name', '')).strip()
        last = str(row.get('Last Name', '')).strip()

        key = (first.lower(), last.lower())

        if key in name_to_rel:
            rel = name_to_rel[key]
            relationships.append(rel)
            sides.append(determine_side(rel))
            matched += 1
        else:
            relationships.append('')
            sides.append('Unknown')
            unmatched += 1

    rsvp_df['Relationship'] = relationships
    rsvp_df['Bride_or_Groom'] = sides

    print(f"  - Matched: {matched} guests")
    print(f"  - Unmatched: {unmatched} guests")

    # Reorder columns to put Relationship and Side near the front
    cols = rsvp_df.columns.tolist()
    # Move Relationship and Bride_or_Groom after Last Name
    new_order = []
    for c in cols:
        new_order.append(c)
        if c == 'Last Name':
            if 'Relationship' in cols:
                new_order.append('Relationship')
            if 'Bride_or_Groom' in cols:
                new_order.append('Bride_or_Groom')

    # Remove duplicates while preserving order
    seen = set()
    final_order = []
    for c in new_order:
        if c not in seen:
            seen.add(c)
            final_order.append(c)

    rsvp_df = rsvp_df[final_order]

    # Save merged data
    rsvp_df.to_csv(output_path, index=False)
    print(f"\nSaved merged data to: {output_path}")

    # Print summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Total guests: {len(rsvp_df)}")
    print(f"\nBy Side:")
    print(rsvp_df['Bride_or_Groom'].value_counts().to_string())

    # Check for potential duplicates (same name, different sides)
    rsvp_df['_fullname'] = rsvp_df['First Name'].fillna('') + ' ' + rsvp_df['Last Name'].fillna('')
    dupes = rsvp_df.groupby('_fullname').filter(lambda x: len(x) > 1)

    if len(dupes) > 0:
        print(f"\n⚠️  Found {len(dupes)} guests with duplicate names:")
        for name in dupes['_fullname'].unique():
            rows = rsvp_df[rsvp_df['_fullname'] == name]
            print(f"\n  '{name}':")
            for _, r in rows.iterrows():
                print(f"    - {r['Relationship']} ({r['Bride_or_Groom']})")

    return rsvp_df


def main():
    parser = argparse.ArgumentParser(description="Merge Zola Guest List and RSVP exports")
    parser.add_argument("--guest-list", type=str, help="Path to Guest List export CSV")
    parser.add_argument("--rsvps", type=str, help="Path to RSVP export CSV")
    parser.add_argument("--output", type=str, help="Output path for merged CSV")
    args = parser.parse_args()

    # Determine file paths
    if args.guest_list and args.rsvps:
        guest_list_path = Path(args.guest_list)
        rsvp_path = Path(args.rsvps)
    else:
        print("Auto-detecting export files in Downloads...")
        downloads = Path.home() / "Downloads"
        guest_list_path, rsvp_path = find_latest_exports(downloads)

        if not guest_list_path:
            print("\n❌ Could not find Guest List export (with 'Relationship To Couple' column)")
            print("   Please export from: Manage guest list → Upload spreadsheet area")
            return

        if not rsvp_path:
            print("\n❌ Could not find RSVP export (with event RSVP columns)")
            print("   Please export from: Track RSVPs → Export RSVPs → .csv format")
            return

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = data_dir / f"merged_rsvps_{timestamp}.csv"

    # Merge the exports
    merged_df = merge_exports(guest_list_path, rsvp_path, output_path)

    print("\n✅ Done!")
    print(f"\nTo update the dashboard:")
    print(f'  cp "{output_path}" site/public/data.csv')


if __name__ == "__main__":
    main()
