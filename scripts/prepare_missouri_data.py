#!/usr/bin/env python3
"""
Prepare Missouri-only subset from large CSV files.

Usage examples:
  # Single file to Parquet
  python scripts/prepare_missouri_data.py ^
      --input data/raw/consult_waits_2024_03_25.csv ^
      --outdir data/processed ^
      --state-col state --state-value MO ^
      --to parquet

  # Multiple files, gzip-CSV output
  python scripts/prepare_missouri_data.py ^
      --input data/raw/*.csv ^
      --outdir data/processed ^
      --state-col state --state-value MO ^
      --to csv.gz
"""

import argparse
import glob
import os
from pathlib import Path
import pandas as pd

def detect_state_column(df, user_col):
    """
    Return a valid state column name in df.
    Priority: user-provided -> common variants -> None
    """
    if user_col and user_col in df.columns:
        return user_col
    candidates = ["state", "State", "STATE", "state_abbrev", "state_code",
                  "state_cd", "st", "jurisdiction", "state_name", "STATE_NAME"]
    for c in candidates:
        if c in df.columns:
            return c
    return None

def is_missouri(value):
    if value is None:
        return False
    s = str(value).strip().upper()
    # Accept common encodings for Missouri
    return s in {"MO", "MISSOURI", "29"}  # 29 = Missouri FIPS state code

def convert_types(df):
    # Optional: put any inexpensive, consistent dtype casts here for stability
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, nargs="+",
                    help="One or more CSV paths (wildcards allowed).")
    ap.add_argument("--outdir", required=True, help="Output directory.")
    ap.add_argument("--state-col", default=None,
                    help="Exact name of the state column if known (optional).")
    ap.add_argument("--state-value", default="MO",
                    help="Value used to filter (default: MO). Ignored if auto-match uses different logic.")
    ap.add_argument("--to", choices=["parquet", "csv.gz", "both"], default="parquet",
                    help="Output format (default parquet).")
    ap.add_argument("--basename", default="missouri_subset",
                    help="Base filename for outputs (default missouri_subset).")
    ap.add_argument("--chunksize", type=int, default=250_000,
                    help="Rows per chunk for streaming (default 250k).")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    files = []
    for pattern in args.input:
        files.extend(sorted(glob.glob(pattern)))
    if not files:
        raise SystemExit("No input files matched.")

    # Accumulate in a local list to write once; for very large results,
    # you can also stream-append to CSV.gz instead of holding in memory.
    collected = []

    for path in files:
        print(f"[INFO] Processing: {path}")
        # If your CSVs have a known encoding or delimiter, set it here
        for i, chunk in enumerate(pd.read_csv(path, chunksize=args.chunksize, low_memory=False)):
            if i == 0:
                state_col = detect_state_column(chunk, args.state_col)
                if not state_col:
                    raise SystemExit(f"Could not detect a state column in {path}. "
                                     f"Pass --state-col to specify it.")
                print(f"[INFO] Using state column: {state_col}")

            # Ensure consistent dtypes if needed
            chunk = convert_types(chunk)

            # Flexible Missouri filter
            mask = chunk[state_col].apply(is_missouri)
            mizz = chunk.loc[mask]
            if not mizz.empty:
                collected.append(mizz)

    if not collected:
        print("[WARN] No Missouri rows found. Exiting without writing outputs.")
        return

    df = pd.concat(collected, ignore_index=True)

    # Optional: select/rename a clean subset of columns here for smaller outputs
    # keep_cols = ["colA","colB","colC"]; df = df[keep_cols]

    # Write outputs
    base = outdir / args.basename
    if args.to in ("parquet", "both"):
        parquet_path = f"{base}.parquet"
        print(f"[INFO] Writing Parquet: {parquet_path}")
        df.to_parquet(parquet_path, index=False)  # snappy by default

    if args.to in ("csv.gz", "both"):
        csv_gz_path = f"{base}.csv.gz"
        print(f"[INFO] Writing gzip CSV: {csv_gz_path}")
        df.to_csv(csv_gz_path, index=False, compression="gzip")

    # Write a simple README with provenance
    readme_path = outdir / f"{args.basename}_PROVENANCE.txt"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            "Provenance for Missouri-only dataset\n"
            "-----------------------------------\n"
            f"Inputs: {len(files)} source file(s)\n"
            "Filter: Records where state ∈ {MO, Missouri, 29(FIPS)}\n"
            "Method: Chunked read with pandas; no row-level transformations beyond filtering.\n"
            "Script: scripts/prepare_missouri_data.py\n"
        )
    print(f"[INFO] Wrote provenance: {readme_path}")

if __name__ == "__main__":
    main()