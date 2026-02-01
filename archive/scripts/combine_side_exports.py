#!/usr/bin/env python3
"""
Combine Side-Filtered RSVP Exports

Combines two RSVP exports (one for bride's side, one for groom's side) into a single
combined CSV file. This approach avoids name collision issues when there are guests
with the same name on different sides.

Usage:
    python combine_side_exports.py --bride bride_rsvps.csv --groom groom_rsvps.csv
    python combine_side_exports.py  # Auto-finds files matching patterns

Expected file naming:
    - Bride's side: *bride*.csv or *saumya*.csv in data/raw/
    - Groom's side: *groom*.csv or *mahek*.csv in data/raw/

Or place files as:
    - data/raw/bride_rsvps.csv
    - data/raw/groom_rsvps.csv
"""

import pandas as pd
import argparse
from datetime import datetime
from pathlib import Path


def find_side_files(data_dir: Path) -> tuple[Path | None, Path | None]:
    """
    Auto-detect bride and groom RSVP files in the raw directory.

    Looks for files containing 'bride' or 'saumya' for bride's side,
    and 'groom' or 'mahek' for groom's side.
    """
    raw_dir = data_dir / "raw"

    bride_file = None
    groom_file = None

    for csv_file in raw_dir.glob("*.csv"):
        name_lower = csv_file.name.lower()

        # Skip combined files and old format files
        if "combined" in name_lower or "guest_list_20" in name_lower or "rsvps_20" in name_lower:
            continue

        if "bride" in name_lower or "saumya" in name_lower:
            bride_file = csv_file
        elif "groom" in name_lower or "mahek" in name_lower:
            groom_file = csv_file

    return bride_file, groom_file


def load_rsvp_file(file_path: Path, side: str) -> pd.DataFrame:
    """
    Load an RSVP CSV file and add side information.

    Args:
        file_path: Path to the CSV file
        side: Either 'Bride' or 'Groom'

    Returns:
        DataFrame with added Side and Bride_or_Groom columns
    """
    df = pd.read_csv(file_path)

    # Add the side column based on which file this came from
    df["Bride_or_Groom"] = side

    # Try to infer relationship from existing columns or set a default
    if "Relationship To Couple" in df.columns:
        df["Side"] = df["Relationship To Couple"]
    elif "Side" in df.columns:
        pass  # Already has Side column
    else:
        # Set a default based on the side
        df["Side"] = f"{'Saumya' if side == 'Bride' else 'Mahek'}'s Guest"

    print(f"Loaded {len(df)} guests from {file_path.name} ({side}'s side)")

    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names and values.
    """
    df = df.copy()

    # Common column name variations to standardize
    column_mapping = {
        "First name": "First Name",
        "Last name": "Last Name",
        "first name": "First Name",
        "last name": "Last Name",
    }

    df.rename(columns=column_mapping, inplace=True)

    # Standardize RSVP values
    event_columns = []
    for col in df.columns:
        if any(event in col.lower() for event in ["vidhi", "haaldi", "wedding", "reception"]):
            event_columns.append(col)

    for col in event_columns:
        if col in df.columns:
            # Fill empty values
            df[col] = df[col].fillna("No Response")
            df[col] = df[col].replace("", "No Response")

            # Standardize values
            df[col] = df[col].apply(lambda x: standardize_rsvp_value(str(x)))

    return df


def standardize_rsvp_value(value: str) -> str:
    """Standardize RSVP status values."""
    value = str(value).strip()
    value_lower = value.lower()

    if value_lower in ["attending", "yes", "accepted"]:
        return "Attending"
    elif value_lower in ["declined", "no", "not attending"]:
        return "Declined"
    elif value_lower in ["not invited", "n/a", "na"]:
        return "Not Invited"
    elif value_lower in ["no response", "pending", "awaiting", ""]:
        return "No Response"
    else:
        return value  # Keep original if unrecognized


def combine_exports(bride_df: pd.DataFrame, groom_df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine bride and groom DataFrames into a single DataFrame.
    """
    # Standardize both DataFrames
    bride_df = standardize_columns(bride_df)
    groom_df = standardize_columns(groom_df)

    # Find common columns
    common_cols = list(set(bride_df.columns) & set(groom_df.columns))

    # Ensure essential columns are present
    essential_cols = ["First Name", "Last Name", "Side", "Bride_or_Groom"]
    for col in essential_cols:
        if col not in common_cols:
            if col not in bride_df.columns:
                bride_df[col] = ""
            if col not in groom_df.columns:
                groom_df[col] = ""
            common_cols.append(col)

    # Combine
    combined_df = pd.concat([bride_df, groom_df], ignore_index=True)

    print(f"\nCombined total: {len(combined_df)} guests")
    print(f"  Bride's side: {len(bride_df)} guests")
    print(f"  Groom's side: {len(groom_df)} guests")

    return combined_df


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Reorder columns for better readability."""
    preferred_order = [
        "Title",
        "First Name",
        "Last Name",
        "Suffix",
        "Saumya's Vidhi & Haaldi",
        "Mahek's Vidhi & Haaldi",
        "Wedding",
        "Reception",
        "Side",
        "Bride_or_Groom"
    ]

    # Get columns that exist in preferred order
    ordered_cols = [col for col in preferred_order if col in df.columns]

    # Add any remaining columns not in preferred order
    remaining_cols = [col for col in df.columns if col not in ordered_cols]

    return df[ordered_cols + remaining_cols]


def save_output(df: pd.DataFrame, data_dir: Path) -> Path:
    """Save the combined data to processed folder."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = data_dir / "processed" / f"combined_{timestamp}.csv"

    # Ensure processed directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

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

    # Check for potential duplicates (same name appearing multiple times)
    df["_full_name"] = df["First Name"].fillna("") + " " + df["Last Name"].fillna("")
    duplicates = df["_full_name"].value_counts()
    duplicates = duplicates[duplicates > 1]

    if len(duplicates) > 0:
        print("\n⚠️  Names appearing multiple times (verify these are different people):")
        for name, count in duplicates.items():
            if name.strip():
                rows = df[df["_full_name"] == name][["First Name", "Last Name", "Side", "Bride_or_Groom"]]
                print(f"\n  '{name}' appears {count} times:")
                for _, row in rows.iterrows():
                    print(f"    - {row['Side']} ({row['Bride_or_Groom']})")

    df.drop("_full_name", axis=1, inplace=True)

    # By RSVP status for Wedding
    if "Wedding" in df.columns:
        print("\nWedding RSVP Status:")
        print(df["Wedding"].value_counts().to_string())


def main():
    parser = argparse.ArgumentParser(description="Combine side-filtered RSVP exports")
    parser.add_argument(
        "--bride",
        type=str,
        default=None,
        help="Path to bride's side RSVP export CSV"
    )
    parser.add_argument(
        "--groom",
        type=str,
        default=None,
        help="Path to groom's side RSVP export CSV"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to data directory (default: ../data relative to script)"
    )
    args = parser.parse_args()

    # Determine data directory
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data"

    print(f"Data directory: {data_dir}")

    # Get file paths
    if args.bride and args.groom:
        bride_path = Path(args.bride)
        groom_path = Path(args.groom)
    else:
        print("\nAuto-detecting bride and groom RSVP files...")
        bride_path, groom_path = find_side_files(data_dir)

        if not bride_path:
            print("\n❌ Could not find bride's side file.")
            print("   Expected: a CSV file with 'bride' or 'saumya' in the name")
            print("   Example: data/raw/bride_rsvps.csv or data/raw/saumya_guests.csv")
            return

        if not groom_path:
            print("\n❌ Could not find groom's side file.")
            print("   Expected: a CSV file with 'groom' or 'mahek' in the name")
            print("   Example: data/raw/groom_rsvps.csv or data/raw/mahek_guests.csv")
            return

        print(f"\nFound files:")
        print(f"  Bride's side: {bride_path.name}")
        print(f"  Groom's side: {groom_path.name}")

    # Verify files exist
    if not bride_path.exists():
        print(f"\n❌ Bride file not found: {bride_path}")
        return
    if not groom_path.exists():
        print(f"\n❌ Groom file not found: {groom_path}")
        return

    # Load files
    print()
    bride_df = load_rsvp_file(bride_path, "Bride")
    groom_df = load_rsvp_file(groom_path, "Groom")

    # Combine
    combined_df = combine_exports(bride_df, groom_df)

    # Reorder columns
    combined_df = reorder_columns(combined_df)

    # Save
    output_path = save_output(combined_df, data_dir)

    # Print summary
    print_summary(combined_df)

    print("\n✅ Done! You can now copy the combined file to the dashboard:")
    print(f"   cp \"{output_path}\" site/public/data.csv")


if __name__ == "__main__":
    main()
