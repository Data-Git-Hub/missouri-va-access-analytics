#!/usr/bin/env python
"""
Clean the Missouri subset of VA/community-care wait-time data.

Inputs (searched in this order unless --input provided):
  - data/processed/consult_waits_state_subset.csv.gz
  - data/raw/consult_waits_state_subset.csv.gz

Output:
  - data/cleaned/mo_waits_clean.csv.gz
  - prints a summary with pre/post counts for your report

Optional:
  - data/reference/stopcode_specialty_map.csv with columns:
      stopcode (int or str), specialty_category in {primary, mental_health, specialty}
"""

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]  # .../missouri-va-access-analytics
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_CLEANED = PROJECT_ROOT / "data" / "cleaned"
DATA_REF = PROJECT_ROOT / "data" / "reference"

DEFAULTS = [
    DATA_PROCESSED / "consult_waits_state_subset.csv.gz",
    DATA_RAW / "consult_waits_state_subset.csv.gz",
]

OUTPUT_PATH = DATA_CLEANED / "mo_waits_clean.csv.gz"
SPECIALTY_MAP = DATA_REF / "stopcode_specialty_map.csv"


def load_input(path_arg: str | None) -> Path:
    if path_arg:
        p = Path(path_arg)
        if not p.exists():
            raise FileNotFoundError(f"Input not found: {p}")
        return p
    for p in DEFAULTS:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"Could not find input file. Searched: {', '.join(str(x) for x in DEFAULTS)}. "
        f"Pass an explicit --input path."
    )


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    # Common date columns seen in this subset: activitydatetime, dta, dts, dtc
    for col in ["activitydatetime", "dta", "dts", "dtc"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    return df


def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    if "dtot" in df.columns:
        df["dtot"] = pd.to_numeric(df["dtot"], errors="coerce")
    if "stopcode" in df.columns:
        df["stopcode"] = pd.to_numeric(df["stopcode"], errors="coerce")
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "month" in df.columns:
        df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
    if "zip" in df.columns:
        df["zip"] = pd.to_numeric(df["zip"], errors="coerce").astype("Int64")
    if "non_va" in df.columns:
        df["non_va"] = pd.to_numeric(df["non_va"], errors="coerce").fillna(0).astype(int)
    return df


def infer_year(df: pd.DataFrame) -> pd.Series:
    if "year" in df.columns and df["year"].notna().any():
        return df["year"].astype("Int64")
    # fallback to dta or activitydatetime
    for col in ["dta", "activitydatetime", "dtc"]:
        if col in df.columns:
            years = df[col].dt.year
            if years.notna().any():
                return years.astype("Int64")
    return pd.Series([pd.NA] * len(df), index=df.index, dtype="Int64")


def filter_missouri(df: pd.DataFrame) -> pd.DataFrame:
    if "state" in df.columns:
        return df[df["state"].astype(str).str.upper() == "MO"].copy()
    # Fallback by ZIP3 if 'state' missing: Missouri ZIP3 roughly 630–658 inclusive
    if "zip" in df.columns:
        z = df["zip"].astype("Int64")
        return df[(z >= 63000) & (z < 65900)].copy()
    return df


def load_specialty_map() -> pd.DataFrame | None:
    if SPECIALTY_MAP.exists():
        m = pd.read_csv(SPECIALTY_MAP)
        m["stopcode"] = pd.to_numeric(m["stopcode"], errors="coerce")
        m["specialty_category"] = m["specialty_category"].astype(str).str.strip().str.lower()
        return m[["stopcode", "specialty_category"]].dropna()
    return None


def derive_fields(df: pd.DataFrame, spec_map: pd.DataFrame | None) -> pd.DataFrame:
    # care_setting
    if "non_va" in df.columns:
        df["care_setting"] = np.where(df["non_va"].fillna(0).astype(int) == 1, "Community", "VA")
    else:
        df["care_setting"] = "VA"

    # veteran_zip3
    if "zip" in df.columns:
        z = df["zip"].astype("Int64")
        df["veteran_zip3"] = (z // 100).astype("Int64")  # 5-digit -> first 3 digits
    else:
        df["veteran_zip3"] = pd.NA

    # wait_days
    if "dtot" in df.columns:
        df["wait_days"] = pd.to_numeric(df["dtot"], errors="coerce")
    else:
        # derive from dates if dtot not present
        if "dta" in df.columns and "dtc" in df.columns:
            df["wait_days"] = (df["dtc"] - df["dta"]).dt.days
        else:
            df["wait_days"] = pd.NA

    # specialty_category
    df["specialty_category"] = "unknown"
    if spec_map is not None and "stopcode" in df.columns:
        df = df.merge(spec_map, on="stopcode", how="left", suffixes=("", "_mapped"))
        df["specialty_category"] = df["specialty_category_mapped"].fillna(df["specialty_category"])
        df = df.drop(columns=["specialty_category_mapped"])

    # met_access_standard
    def threshold(row):
        cat = str(row["specialty_category"]).lower()
        wd = row["wait_days"]
        if pd.isna(wd):
            return pd.NA
        if cat in {"primary", "mental_health"}:
            return int(wd <= 20)
        # default and specialty:
        return int(wd <= 28)

    df["met_access_standard"] = df.apply(threshold, axis=1)
    return df


def main():
    parser = argparse.ArgumentParser(description="Clean Missouri wait-time data.")
    parser.add_argument("--input", help="Path to input CSV[.gz]. Optional.")
    parser.add_argument("--output", help="Override output path", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    inp = load_input(args.input)
    outp = Path(args.output)

    print(f"[INFO] Reading: {inp}")
    df = pd.read_csv(inp, low_memory=False, compression="infer")
    n_raw_rows, n_raw_cols = df.shape

    df = parse_dates(df)
    df = coerce_numeric(df)
    # add year if missing
    df["__year"] = infer_year(df)
    # filter Missouri and window
    df = filter_missouri(df)
    df = df[(df["__year"] >= 2014) & (df["__year"] <= 2025)].copy()

    # drop exact duplicates on a conservative subset of keys if present
    dedup_keys = [c for c in ["patientsid", "activitydatetime", "sta3n", "stopcode", "non_va", "dtot"] if c in df.columns]
    before_dedup = len(df)
    if dedup_keys:
        df = df.drop_duplicates(subset=dedup_keys)
    else:
        df = df.drop_duplicates()
    removed_dups = before_dedup - len(df)

    # derive fields
    spec_map = load_specialty_map()
    df = derive_fields(df, spec_map)

    # ensure cleaned dir
    outp.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(outp, index=False, compression="infer")

    # summary
    print("==== CLEANING SUMMARY ====")
    print(f"Raw (all MO subset): {n_raw_rows} rows, {n_raw_cols} cols")
    print(f"After window/filter:  {len(df) + removed_dups} rows (before de-dup)")
    print(f"Duplicates removed:   {removed_dups}")
    print(f"Final (analysis):     {len(df)} rows, {df.shape[1]} cols")
    # attribute list
    print("Attributes (final):")
    print(", ".join(df.columns))


if __name__ == "__main__":
    main()
