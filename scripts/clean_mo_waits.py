#!/usr/bin/env python
"""
Clean Missouri VA/community-care wait-time data and emit:
  - data/cleaned/cleaned_mo_waits.csv.gz
  - data/cleaned/cleaning_summary.csv
"""

from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
import numpy as np
import pandas as pd

# --- Project paths ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_CLEANED = PROJECT_ROOT / "data" / "cleaned"
DATA_REF = PROJECT_ROOT / "data" / "reference"

DEFAULT_INPUTS = [
    DATA_PROCESSED / "consult_waits_state_subset.csv.gz",
    DATA_RAW / "consult_waits_state_subset.csv.gz",
]

DEFAULT_OUTPUT = DATA_CLEANED / "cleaned_mo_waits.csv.gz"
SPECIALTY_MAP = DATA_REF / "stopcode_specialty_map.csv"

STATE_FULL_NAME = {
    "AL":"ALABAMA","AK":"ALASKA","AZ":"ARIZONA","AR":"ARKANSAS","CA":"CALIFORNIA","CO":"COLORADO",
    "CT":"CONNECTICUT","DE":"DELAWARE","FL":"FLORIDA","GA":"GEORGIA","HI":"HAWAII","ID":"IDAHO",
    "IL":"ILLINOIS","IN":"INDIANA","IA":"IOWA","KS":"KANSAS","KY":"KENTUCKY","LA":"LOUISIANA",
    "ME":"MAINE","MD":"MARYLAND","MA":"MASSACHUSETTS","MI":"MICHIGAN","MN":"MINNESOTA",
    "MS":"MISSISSIPPI","MO":"MISSOURI","MT":"MONTANA","NE":"NEBRASKA","NV":"NEVADA","NH":"NEW HAMPSHIRE",
    "NJ":"NEW JERSEY","NM":"NEW MEXICO","NY":"NEW YORK","NC":"NORTH CAROLINA","ND":"NORTH DAKOTA",
    "OH":"OHIO","OK":"OKLAHOMA","OR":"OREGON","PA":"PENNSYLVANIA","RI":"RHODE ISLAND",
    "SC":"SOUTH CAROLINA","SD":"SOUTH DAKOTA","TN":"TENNESSEE","TX":"TEXAS","UT":"UTAH","VT":"VERMONT",
    "VA":"VIRGINIA","WA":"WASHINGTON","WV":"WEST VIRGINIA","WI":"WISCONSIN","WY":"WYOMING",
    "DC":"DISTRICT OF COLUMBIA","PR":"PUERTO RICO"
}

def log(msg: str) -> None:
    print(f"[INFO] {msg}")

def warn(msg: str) -> None:
    print(f"[WARN] {msg}", file=sys.stderr)

def err(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)

def load_input(path_arg: str | None) -> Path:
    if path_arg:
        p = Path(path_arg)
        if p.exists():
            return p
        raise FileNotFoundError(f"Input not found: {p}")
    for p in DEFAULT_INPUTS:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Could not find input file. Searched:\n  - "
        + "\n  - ".join(str(x) for x in DEFAULT_INPUTS)
        + "\nPass --input to specify a file."
    )

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["activitydatetime", "dta", "dts", "dtc"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    return df

def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["dtot", "stopcode", "year", "month", "zip", "non_va", "sta3n"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "non_va" in df.columns:
        df["non_va"] = df["non_va"].fillna(0).astype(int)
    return df

def infer_year(df: pd.DataFrame) -> pd.Series:
    if "year" in df.columns and df["year"].notna().any():
        return df["year"].astype("Int64")
    for c in ["dta", "activitydatetime", "dtc"]:
        if c in df.columns:
            years = df[c].dt.year
            if years.notna().any():
                return years.astype("Int64")
    return pd.Series([pd.NA] * len(df), index=df.index, dtype="Int64")

def normalize_state_series(s: pd.Series) -> pd.Series:
    if s is None:
        return s
    up = s.astype(str).str.strip().str.upper()
    full_to_code = {v: k for k, v in STATE_FULL_NAME.items()}

    def normalize_one(val: str) -> str:
        if val in STATE_FULL_NAME:  # already code like 'MO'
            return val
        val_clean = re.sub(r"[^A-Z]", " ", val)
        tokens = [t for t in val_clean.split() if t]
        for t in tokens:
            if t in STATE_FULL_NAME:
                return t
        for t in tokens:
            if t in full_to_code:
                return full_to_code[t]
        if val in full_to_code:
            return full_to_code[val]
        return val

    return up.map(normalize_one)

def filter_state_auto(df: pd.DataFrame, state_abbrev: str, debug_states: bool=False) -> tuple[pd.DataFrame, str]:
    abbr = state_abbrev.upper()
    if "state" in df.columns:
        norm = normalize_state_series(df["state"])
        if debug_states:
            print("[DEBUG] Top normalized state values:")
            print(norm.value_counts().head(20))
        out = df[norm == abbr].copy()
        log(f"Normalized state filter == {abbr}: {len(out)} rows")
        if len(out) > 0:
            return out, "state"
        warn(f"No rows matched normalized state == {abbr}. Trying ZIP fallback (if MO).")

    if abbr == "MO" and "zip" in df.columns:
        z = df["zip"].astype("Int64")
        out = df[(z >= 63000) & (z < 65900)].copy()
        log(f"ZIP-range fallback for MO (63000–65899): {len(out)} rows")
        return out, "zip"

    warn("No usable state filter applied (no match and no ZIP fallback).")
    return df, "none"

def load_specialty_map() -> pd.DataFrame | None:
    if SPECIALTY_MAP.exists():
        m = pd.read_csv(SPECIALTY_MAP)
        m["stopcode"] = pd.to_numeric(m["stopcode"], errors="coerce")
        m["specialty_category"] = m["specialty_category"].astype(str).str.strip().str.lower()
        return m[["stopcode", "specialty_category"]].dropna()
    return None

def derive_fields(df: pd.DataFrame, spec_map: pd.DataFrame | None) -> pd.DataFrame:
    df["care_setting"] = np.where(df.get("non_va", 0) == 1, "Community", "VA")
    if "zip" in df.columns:
        z = df["zip"].astype("Int64")
        df["veteran_zip3"] = (z // 100).astype("Int64")
    else:
        df["veteran_zip3"] = pd.NA

    if "dtot" in df.columns:
        df["wait_days"] = pd.to_numeric(df["dtot"], errors="coerce")
    elif all(c in df.columns for c in ["dta", "dtc"]):
        df["wait_days"] = (df["dtc"] - df["dta"]).dt.days
    else:
        df["wait_days"] = pd.NA

    df["specialty_category"] = "unknown"
    if spec_map is not None and "stopcode" in df.columns:
        df = df.merge(spec_map, on="stopcode", how="left", suffixes=("", "_mapped"))
        df["specialty_category"] = df["specialty_category_mapped"].fillna(df["specialty_category"])
        df = df.drop(columns=["specialty_category_mapped"])

    def threshold(row) -> int | pd.NA:
        wd = row["wait_days"]
        if pd.isna(wd):
            return pd.NA
        cat = str(row["specialty_category"]).lower()
        if cat in {"primary", "mental_health"}:
            return int(wd <= 20)
        return int(wd <= 28)

    df["met_access_standard"] = df.apply(threshold, axis=1)
    return df

def save_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, compression="infer")
    log(f"Wrote: {path}  ({len(df)} rows, {df.shape[1]} cols)")

def main():
    parser = argparse.ArgumentParser(description="Clean Missouri wait-time data.")
    parser.add_argument("--input", help="Path to input CSV[.gz] (optional).")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to cleaned CSV (optional).")
    parser.add_argument("--state", default="MO", help="Two-letter state filter (default: MO).")
    parser.add_argument("--year-min", type=int, default=2014, help="Min year inclusive.")
    parser.add_argument("--year-max", type=int, default=2025, help="Max year inclusive.")
    parser.add_argument("--no-dedup", action="store_true", help="Skip de-duplication.")
    parser.add_argument("--debug-states", action="store_true", help="Print normalized state values.")
    args = parser.parse_args()

    try:
        inp = load_input(args.input)
    except FileNotFoundError as e:
        err(str(e)); sys.exit(2)

    outp = Path(args.output)

    log(f"Project root: {PROJECT_ROOT}")
    log(f"Reading: {inp}")
    try:
        df = pd.read_csv(inp, low_memory=False, compression="infer")
    except Exception as e:
        err(f"Failed to read input: {e}"); sys.exit(3)

    n_raw_rows, n_raw_cols = df.shape
    log(f"Raw shape: {n_raw_rows} rows, {n_raw_cols} cols")
    log(f"Columns: {', '.join(df.columns[:20])}{' ...' if len(df.columns)>20 else ''}")

    # Coercions and derived year
    df = parse_dates(df)
    df = coerce_numeric(df)
    df["__year"] = infer_year(df)

    # Robust state filter with fallback
    df, filter_mode = filter_state_auto(df, args.state, debug_states=args.debug_states)

    # Year window
    before_window = len(df)
    df = df[(df["__year"] >= args.year_min) & (df["__year"] <= args.year_max)].copy()
    after_window = len(df)
    log(f"Year window {args.year_min}-{args.year_max}: {before_window} -> {after_window} rows")

    # De-dup
    removed_dups = 0
    if not args.no_dedup:
        keys = [c for c in ["patientsid", "activitydatetime", "sta3n", "stopcode", "non_va", "dtot"] if c in df.columns]
        before = len(df)
        df = df.drop_duplicates(subset=keys) if keys else df.drop_duplicates()
        removed_dups = before - len(df)
        log(f"De-dup removed: {removed_dups} rows")
    else:
        log("Skipping de-duplication (--no-dedup).")

    # Derive fields and save
    spec_map = load_specialty_map()
    if spec_map is None:
        log("No specialty map found; 'specialty_category' remains 'unknown' (28-day threshold) unless provided.")
    df = derive_fields(df, spec_map)

    # ALWAYS write outputs (even if 0 rows) so artifacts exist
    DATA_CLEANED.mkdir(parents=True, exist_ok=True)
    save_csv(df, outp)

    # Summary CSV for Overleaf
    after_filter_before_dedup = after_window + removed_dups
    summary_rows = [
        {"Metric": "Records (raw Missouri subset)", "Count": n_raw_rows},
        {"Metric": f"Records after {args.year_min}–{args.year_max} filter", "Count": after_filter_before_dedup},
        {"Metric": "Exact duplicates removed", "Count": removed_dups},
        {"Metric": "Final records (analysis-ready)", "Count": len(df)},
        {"Metric": "Attributes (raw)", "Count": n_raw_cols},
        {"Metric": "Attributes (analysis-ready)", "Count": df.shape[1]},
    ]
    pd.DataFrame(summary_rows).to_csv(DATA_CLEANED / "cleaning_summary.csv", index=False)
    log(f"Wrote summary table: {DATA_CLEANED / 'cleaning_summary.csv'}")

    # Console recap
    print("\n==== CLEANING SUMMARY ====")
    print(f"State filter mode: {filter_mode}")
    print(f"Raw (all MO subset): {n_raw_rows} rows, {n_raw_cols} cols")
    print(f"After window/filter:  {after_filter_before_dedup} rows (before de-dup)")
    print(f"Duplicates removed:   {removed_dups}")
    print(f"Final (analysis):     {len(df)} rows, {df.shape[1]} cols")
    print("Attributes (final):")
    print(", ".join(df.columns))

if __name__ == "__main__":
    main()
