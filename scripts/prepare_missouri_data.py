#!/usr/bin/env python3
"""
prepare_missouri_data.py

Stream-read large VA consults CSV files, tolerate malformed rows, filter by state,
and write a clean subset for reproducibility.

Features
- Handles one file or many (glob patterns).
- Tolerant CSV parsing (engine="python", on_bad_lines="skip").
- Keeps ZIP codes as text (preserves leading zeros) when present.
- Parses activitydatetime when present.
- Streaming writer:
    * CSV / CSV.GZ: single output file (append mode, header once).
    * Parquet: writes chunked part files (…_part-00001.parquet, etc.).
- Logs per-file and total row counts.

Usage examples (PowerShell on Windows):
    python scripts\\prepare_missouri_data.py `
      --input data\\raw\\consult_waits_2024_03_25.csv `
      --outdir data\\processed `
      --state-value MISSOURI `
      --to csv.gz

    python scripts\\prepare_missouri_data.py `
      --input "data\\raw\\*.csv" `
      --outdir data\\processed `
      --state-value MISSOURI `
      --state-col state `
      --to parquet
"""

from __future__ import annotations

import argparse
import glob
import logging
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd


def configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=level,
    )


def discover_files(pattern: str) -> List[Path]:
    paths = [Path(p) for p in glob.glob(pattern)]
    if not paths:
        raise FileNotFoundError(f"No input files found for pattern: {pattern}")
    return paths


def read_header_columns(csv_path: Path) -> List[str]:
    # Parse only header to learn available columns
    df0 = pd.read_csv(csv_path, nrows=0, engine="python")
    return df0.columns.tolist()


def make_reader(
    csv_path: Path,
    chunksize: int,
    zip_col_name: str = "zip",
    dt_col_name: str = "activitydatetime",
) -> Iterable[pd.DataFrame]:
    cols = read_header_columns(csv_path)
    converters = {}
    parse_dates: List[str] = []

    if zip_col_name in cols:
        converters[zip_col_name] = str  # preserve leading zeros

    if dt_col_name in cols:
        parse_dates = [dt_col_name]

    # Tolerant reader
    reader = pd.read_csv(
        csv_path,
        chunksize=chunksize,
        engine="python",          # tolerant with irregular rows
        on_bad_lines="skip",      # skip malformed lines (wrong field count)
        sep=",",
        quotechar='"',
        low_memory=False,
        converters=converters if converters else None,
        parse_dates=parse_dates if parse_dates else None,
        infer_datetime_format=True,
        keep_default_na=True,
    )
    return reader


def normalize_state(series: pd.Series) -> pd.Series:
    # Ensure string, strip whitespace, uppercase
    return series.astype("string").str.strip().str.upper()


def state_filter(
    df: pd.DataFrame,
    state_col: str,
    allowed_states_norm: List[str],
) -> pd.DataFrame:
    if state_col not in df.columns:
        raise KeyError(f"State column '{state_col}' not found in input data.")
    s = normalize_state(df[state_col])
    return df[s.isin(allowed_states_norm)]


class CSVStreamWriter:
    def __init__(self, outpath: Path, compress: bool):
        self.outpath = outpath
        self.compress = compress
        self._wrote_header = False
        self.outpath.parent.mkdir(parents=True, exist_ok=True)

    def write(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        mode = "a"
        header = not self._wrote_header
        if self.compress:
            df.to_csv(self.outpath, mode=mode, index=False, header=header, compression="gzip")
        else:
            df.to_csv(self.outpath, mode=mode, index=False, header=header)
        self._wrote_header = True


class ParquetChunkWriter:
    def __init__(self, outdir: Path, base: str):
        self.outdir = outdir
        self.base = base
        self.counter = 0
        self.outdir.mkdir(parents=True, exist_ok=True)

    def write(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        self.counter += 1
        part = f"{self.base}_part-{self.counter:05d}.parquet"
        target = self.outdir / part
        # Requires pyarrow installed
        df.to_parquet(target, index=False)


def build_output_targets(
    outdir: Path,
    to_format: str,
    basename_hint: Optional[str] = None,
) -> dict:
    """
    Returns a dict with keys:
      - kind: 'csv', 'csv.gz', or 'parquet'
      - path: Path (for csv/csv.gz) or None
      - base: str (for parquet file prefix) or None
    """
    outdir.mkdir(parents=True, exist_ok=True)
    if to_format == "csv":
        path = outdir / "consult_waits_state_subset.csv"
        return {"kind": "csv", "path": path, "base": None}
    elif to_format == "csv.gz":
        path = outdir / "consult_waits_state_subset.csv.gz"
        return {"kind": "csv.gz", "path": path, "base": None}
    elif to_format == "parquet":
        # Write chunked part files with a stable base name
        base = (basename_hint or "consult_waits_state_subset").replace(".parquet", "")
        return {"kind": "parquet", "path": None, "base": base}
    else:
        raise ValueError(f"Unknown output format: {to_format}")


def process_files(
    in_files: List[Path],
    outdir: Path,
    to_format: str,
    state_col: str,
    states: List[str],
    chunksize: int,
) -> None:
    allowed_states_norm = [s.strip().upper() for s in states]
    total_in = 0
    total_out = 0
    total_bad_empty_rows = 0

    # Prepare writers
    targets = build_output_targets(outdir, to_format)
    if targets["kind"] == "csv":
        writer = CSVStreamWriter(targets["path"], compress=False)
    elif targets["kind"] == "csv.gz":
        writer = CSVStreamWriter(targets["path"], compress=True)
    else:
        writer = ParquetChunkWriter(outdir, targets["base"])

    for fpath in in_files:
        logging.info(f"Processing: {fpath}")
        in_rows = 0
        out_rows = 0
        empty_rows = 0

        for i, chunk in enumerate(make_reader(fpath, chunksize=chunksize)):
            # Count obviously broken rows (rare; rows that became fully NaN)
            broken = chunk[chunk.isna().all(axis=1)]
            if not broken.empty:
                empty_rows += len(broken)

            try:
                filtered = state_filter(chunk, state_col, allowed_states_norm)
            except KeyError as e:
                raise

            in_rows += len(chunk)
            out_rows += len(filtered)

            # Write
            writer.write(filtered)

            if (i + 1) % 10 == 0:
                logging.info(
                    f"  …chunks processed: {i+1:,} | in_rows={in_rows:,} | out_rows={out_rows:,}"
                )

        logging.info(
            f"Done: {fpath.name} | in_rows={in_rows:,} | out_rows={out_rows:,} | empty_rows={empty_rows:,}"
        )
        total_in += in_rows
        total_out += out_rows
        total_bad_empty_rows += empty_rows

    logging.info(
        f"ALL FILES | total_in={total_in:,} | total_out={total_out:,} | empty_rows={total_bad_empty_rows:,}"
    )
    if total_out == 0:
        logging.warning("No rows matched the requested state filter.")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Filter large VA consult CSVs by state and export a reproducible subset."
    )
    p.add_argument(
        "--input",
        required=True,
        help='Path or glob to CSVs, e.g., "data/raw/consult_waits_2024_03_25.csv" or "data/raw/*.csv"',
    )
    p.add_argument(
        "--outdir",
        required=True,
        type=Path,
        help="Output directory for processed data.",
    )
    p.add_argument(
        "--state-col",
        default="state",
        help="Column name containing state (default: state).",
    )
    p.add_argument(
        "--state-value",
        action="append",
        default=["MISSOURI"],
        help=(
            "State value to include (exact match after uppercasing/strip). "
            "Provide multiple --state-value options to include several. Default: MISSOURI"
        ),
    )
    p.add_argument(
        "--to",
        choices=["csv", "csv.gz", "parquet"],
        default="csv.gz",
        help="Output format. Default: csv.gz",
    )
    p.add_argument(
        "--chunksize",
        type=int,
        default=250_000,
        help="Number of rows per chunk to stream-process. Default: 250000",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (-v for INFO, -vv for DEBUG).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    files = discover_files(args.input)
    logging.info(f"Discovered {len(files)} file(s).")

    try:
        process_files(
            in_files=files,
            outdir=args.outdir,
            to_format=args.to,
            state_col=args.state_col,
            states=args.state_value,
            chunksize=args.chunksize,
        )
    except Exception as e:
        logging.exception("Processing failed.")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
