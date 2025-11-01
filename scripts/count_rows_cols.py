#!/usr/bin/env python3
"""
count_rows_cols.py

Counts the number of rows and columns in the processed dataset file:
data/processed/consult_waits_state_subset.csv.gz

Usage (from the project root or scripts folder):
    python scripts/count_rows_cols.py
"""

from pathlib import Path
import pandas as pd

def main():
    # Define the path relative to the project root
    file_path = Path("data/processed/consult_waits_state_subset.csv.gz")

    # Ensure the file exists
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path.resolve()}")
        return

    print(f"[INFO] Reading: {file_path}")
    try:
        # Read the file (pandas can handle gzip automatically)
        df = pd.read_csv(file_path)

        # Get row and column counts
        rows, cols = df.shape

        print(f"[RESULT] File: {file_path.name}")
        print(f"  Rows: {rows:,}")
        print(f"  Columns: {cols:,}")

    except Exception as e:
        print(f"[ERROR] Failed to read file: {e}")

if __name__ == "__main__":
    main()
