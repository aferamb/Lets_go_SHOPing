#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from advanced_generator_lib import write_advanced_problem
from jshop_runner_lib import JSHOP2Error, run_jshop2
from scenarios_lib import SCENARIOS, build_scenario_problem, scenario_by_name, validate_scenario


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the deterministic advanced scenario suite.")
    parser.add_argument("--suite", default="advanced", help="Only `advanced` is implemented.")
    parser.add_argument("--scenario", action="append", default=[], help="Run only the named scenario(s).")
    parser.add_argument("--plans", type=int, default=1, help="Maximum number of plans requested.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Timeout in seconds per JSHOP2 stage.")
    parser.add_argument(
        "--results-dir",
        default=str(ROOT / ".cache" / "scenarios" / "advanced"),
        help="Directory where scenario problems and results are written.",
    )
    parser.add_argument("--keep-staging", action="store_true", help="Keep JSHOP2 staging directories.")
    return parser.parse_args()


def selected_scenarios(names: list[str]) -> list:
    if not names:
        return list(SCENARIOS)
    return [scenario_by_name(name) for name in names]


def main() -> int:
    args = parse_args()
    if args.suite != "advanced":
        print("Only the `advanced` scenario suite is available.", file=sys.stderr)
        return 1

    domain_path = ROOT / "domains" / "advanced" / "domain.jshop"
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    summary: list[dict[str, object]] = []
    failed = False

    for spec in selected_scenarios(args.scenario):
        scenario_dir = results_dir / spec.name
        scenario_dir.mkdir(parents=True, exist_ok=True)
        problem = build_scenario_problem(spec)
        problem_path = scenario_dir / f"{spec.name}.problem.jshop"
        write_advanced_problem(problem, problem_path)

        entry: dict[str, object] = {
            "scenario": spec.name,
            "description": spec.description,
            "problem_file": str(problem_path),
            "status": "error",
            "errors": [],
            "time_used_s": None,
            "plan_cost": None,
            "plan_length": None,
        }

        try:
            result = run_jshop2(
                domain_path,
                problem_path,
                plan_limit=args.plans,
                keep_staging=args.keep_staging,
                timeout_s=args.timeout,
            )
            errors = validate_scenario(spec, result)
            raw_path = scenario_dir / f"{spec.name}.stdout.txt"
            json_path = scenario_dir / f"{spec.name}.result.json"
            raw_path.write_text(result.planner_stdout, encoding="utf-8")
            json_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

            entry["time_used_s"] = result.time_used_s
            if result.plans:
                entry["plan_cost"] = result.plans[0].cost
                entry["plan_length"] = len(result.plans[0].actions)
            entry["errors"] = errors
            entry["status"] = "passed" if not errors else "failed"
            failed = failed or bool(errors)
        except JSHOP2Error as exc:
            entry["errors"] = [str(exc)]
            failed = True

        summary.append(entry)
        print(f"{spec.name}: {entry['status']}")
        for error in entry["errors"]:
            print(f"  - {error}")

    summary_json = results_dir / "summary.json"
    summary_md = results_dir / "summary.md"
    summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Advanced scenario suite",
        "",
        f"- Domain: `{domain_path}`",
        f"- Timeout per stage: `{args.timeout}`",
        "",
        "| scenario | status | time_used_s | plan_cost | plan_length |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in summary:
        lines.append(
            f"| {entry['scenario']} | {entry['status']} | {entry['time_used_s']} | "
            f"{entry['plan_cost']} | {entry['plan_length']} |"
        )
        for error in entry["errors"]:
            lines.append(f"|  | error | `{error}` |  |  |")
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(summary_json)
    print(summary_md)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
