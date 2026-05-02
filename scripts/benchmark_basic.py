#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASELINE = ROOT / "references" / "pl1_part1_ex12_ff_baseline.csv"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from basic_generator_lib import BasicProblemOptions, write_basic_problem
from jshop_runner_lib import JSHOP2Error, run_jshop2


@dataclass(frozen=True)
class BaselineEntry:
    status: str
    time_s: float | None
    plan_length: int | None


@dataclass(frozen=True)
class BaselineDataset:
    path: Path
    exists: bool
    label: str
    metric_name: str
    rows: dict[int, BaselineEntry]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark the basic SHOP2 domain with growing instance sizes.")
    parser.add_argument("--min-size", type=int, default=2, help="Minimum size with l=p=c=g.")
    parser.add_argument("--max-size", type=int, default=8, help="Maximum size with l=p=c=g.")
    parser.add_argument("--step", type=int, default=1, help="Size step.")
    parser.add_argument("--drones", type=int, default=1, help="Number of drones.")
    parser.add_argument("--carriers", type=int, default=0, help="Compatibility flag from PL1.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Timeout in seconds per JSHOP2 stage.")
    parser.add_argument("--plans", type=int, default=1, help="Maximum number of plans requested.")
    parser.add_argument("--seed-base", type=int, default=0, help="Base seed. Use -1 to disable deterministic seeds.")
    parser.add_argument(
        "--results-dir",
        default=str(ROOT / ".cache" / "benchmarks" / "basic"),
        help="Directory where CSV/MD/problem files are written.",
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE),
        help="Reference CSV from PL1 Exercise 1.2 (FF benchmark); legacy BFS CSVs are still accepted.",
    )
    return parser.parse_args()


def _parse_optional_float(raw: str | None) -> float | None:
    if raw is None or raw == "":
        return None
    return float(raw)


def _parse_optional_int(raw: str | None) -> int | None:
    if raw is None or raw == "":
        return None
    return int(raw)


def load_baseline(path: str | Path) -> BaselineDataset:
    baseline_path = Path(path)
    if not baseline_path.exists():
        return BaselineDataset(
            path=baseline_path,
            exists=False,
            label="No baseline loaded",
            metric_name="",
            rows={},
        )

    with baseline_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])

        if not {"size", "status"}.issubset(fieldnames):
            raise ValueError(f"Unsupported baseline CSV `{baseline_path}`: missing `size` or `status` columns.")

        if {"ff_time_s", "plan_steps"}.issubset(fieldnames):
            label = "PL1 Exercise 1.2 (FF)"
            metric_name = "ff_time_s"
            time_key = "ff_time_s"
            plan_key = "plan_steps"
        elif {"ff_time_s", "plan_length"}.issubset(fieldnames):
            label = "PL1 Exercise 1.2 (FF)"
            metric_name = "ff_time_s"
            time_key = "ff_time_s"
            plan_key = "plan_length"
        elif {"search_time_s", "plan_length"}.issubset(fieldnames):
            label = "PL1 BFS baseline (legacy)"
            metric_name = "search_time_s"
            time_key = "search_time_s"
            plan_key = "plan_length"
        else:
            raise ValueError(
                f"Unsupported baseline CSV `{baseline_path}`: expected FF or legacy BFS benchmark columns."
            )

        rows: dict[int, BaselineEntry] = {}
        for row in reader:
            size = int(row["size"])
            rows[size] = BaselineEntry(
                status=row["status"],
                time_s=_parse_optional_float(row.get(time_key)),
                plan_length=_parse_optional_int(row.get(plan_key)),
            )

    return BaselineDataset(
        path=baseline_path,
        exists=True,
        label=label,
        metric_name=metric_name,
        rows=rows,
    )


def maybe_plot(csv_rows: list[dict[str, str]], baseline: BaselineDataset, output_png: Path) -> bool:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return False

    solved_rows = [row for row in csv_rows if row["status"] == "solved"]
    if not solved_rows:
        return False

    x_values = [int(row["size"]) for row in solved_rows]
    y_values = [float(row["time_used_s"]) for row in solved_rows]

    plt.figure(figsize=(8, 4.5))
    plt.plot(x_values, y_values, marker="o", label="JSHOP2")

    baseline_sizes = []
    baseline_times = []
    for size in sorted(baseline.rows):
        row = baseline.rows[size]
        if row.status == "solved" and row.time_s is not None:
            baseline_sizes.append(size)
            baseline_times.append(row.time_s)
    if baseline_sizes:
        plt.plot(baseline_sizes, baseline_times, marker="s", label=baseline.label)

    plt.xlabel("Problem size (l=p=c=g)")
    plt.ylabel("Planning time (s)")
    if baseline_sizes:
        plt.title(f"Basic SHOP2 benchmark vs {baseline.label}")
    else:
        plt.title("Basic SHOP2 benchmark")
    plt.grid(True, alpha=0.3)
    plt.legend()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_png)
    plt.close()
    return True


def main() -> int:
    args = parse_args()
    results_dir = Path(args.results_dir)
    problems_dir = results_dir / "problems"
    problems_dir.mkdir(parents=True, exist_ok=True)

    domain_path = ROOT / "domains" / "basic" / "domain.jshop"
    baseline = load_baseline(args.baseline)
    rows: list[dict[str, str]] = []

    for size in range(args.min_size, args.max_size + 1, args.step):
        seed = None if args.seed_base < 0 else args.seed_base + size
        options = BasicProblemOptions(
            drones=args.drones,
            carriers=args.carriers,
            locations=size,
            persons=size,
            crates=size,
            goals=size,
            seed=seed,
        )
        problem_path = problems_dir / f"size_{size}.jshop"
        write_basic_problem(options, problem_path)

        baseline_entry = baseline.rows.get(size)
        row = {
            "size": str(size),
            "problem_file": str(problem_path),
            "status": "error",
            "time_used_s": "",
            "plan_cost": "",
            "plan_length": "",
            "baseline_time_s": "" if baseline_entry is None or baseline_entry.time_s is None else f"{baseline_entry.time_s:.6f}",
            "baseline_plan_length": (
                "" if baseline_entry is None or baseline_entry.plan_length is None else str(baseline_entry.plan_length)
            ),
            "baseline_label": baseline.label if baseline.rows else "",
            "baseline_metric": baseline.metric_name,
            "error": "",
        }
        try:
            result = run_jshop2(
                domain_path,
                problem_path,
                plan_limit=args.plans,
                timeout_s=args.timeout,
            )
            first_plan = result.plans[0] if result.plans else None
            row["status"] = "solved" if result.plan_count > 0 else "unsolved"
            row["time_used_s"] = "" if result.time_used_s is None else f"{result.time_used_s:.6f}"
            row["plan_cost"] = "" if first_plan is None else f"{first_plan.cost:.6f}"
            row["plan_length"] = "" if first_plan is None else str(len(first_plan.actions))
        except JSHOP2Error as exc:
            row["status"] = "error"
            row["error"] = str(exc).replace("\n", " | ")
        rows.append(row)
        print(f"size={size} status={row['status']} time={row['time_used_s'] or '-'}")

    csv_path = results_dir / "benchmark_basic.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md_path = results_dir / "benchmark_basic.md"
    lines = [
        "# Benchmark basic SHOP2 domain",
        "",
        f"- Domain: `{domain_path}`",
        f"- Results dir: `{results_dir}`",
        f"- Timeout per stage: `{args.timeout}`",
        f"- Baseline: `{baseline.label}`",
        f"- Baseline CSV: `{baseline.path}`",
        f"- Baseline metric: `{baseline.metric_name or 'n/a'}`",
        "",
        "| size | status | time_used_s | plan_cost | plan_length | baseline_time_s | baseline_plan_length |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['size']} | {row['status']} | {row['time_used_s']} | "
            f"{row['plan_cost']} | {row['plan_length']} | "
            f"{row['baseline_time_s']} | {row['baseline_plan_length']} |"
        )
    png_path = results_dir / "benchmark_basic.png"
    plotted = maybe_plot(rows, baseline, png_path)
    if plotted:
        lines.extend(["", f"![benchmark_basic]({png_path.name})"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(csv_path)
    print(md_path)
    if plotted:
        print(png_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
