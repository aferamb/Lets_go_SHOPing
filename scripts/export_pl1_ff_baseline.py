#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = ROOT.parent.parent / "PL1" / "Planning-practice" / "parte1" / "results"
DEFAULT_OUTPUT = ROOT / "references" / "pl1_part1_ex12_ff_baseline.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize a PL1 Exercise 1.2 FF benchmark CSV into the vendored PL2 baseline format."
    )
    parser.add_argument(
        "--source-csv",
        default=None,
        help="Optional PL1 benchmark_ff_*.csv path. Defaults to the most recent benchmark_ff_*.csv in PL1 results.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Normalized baseline CSV output path.",
    )
    return parser.parse_args()


def default_source_csv(results_dir: str | Path = DEFAULT_RESULTS_DIR) -> Path:
    results_path = Path(results_dir)
    candidates = sorted(results_path.glob("benchmark_ff_*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No benchmark_ff_*.csv files were found in `{results_path}`.")
    return candidates[0]


def export_baseline(source_csv: str | Path, output_csv: str | Path) -> Path:
    source_path = Path(source_csv)
    output_path = Path(output_csv)

    with source_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        required = {"size", "status", "ff_time_s", "wall_time_s", "plan_steps"}
        if not required.issubset(fieldnames):
            missing = ", ".join(sorted(required - fieldnames))
            raise ValueError(f"Unsupported PL1 FF CSV `{source_path}`. Missing columns: {missing}")

        rows = [
            {
                "size": row["size"],
                "status": row["status"],
                "ff_time_s": row["ff_time_s"],
                "wall_time_s": row["wall_time_s"],
                "plan_length": row["plan_steps"],
            }
            for row in reader
        ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["size", "status", "ff_time_s", "wall_time_s", "plan_length"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def main() -> int:
    args = parse_args()
    source_path = Path(args.source_csv) if args.source_csv is not None else default_source_csv()
    output_path = export_baseline(source_path, args.output)
    print(f"Source CSV: {source_path}")
    print(f"Output CSV: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
