#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from jshop_runner_lib import JSHOP2Error, run_jshop2, write_result_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a SHOP2/JSHOP2 domain and problem.")
    parser.add_argument("--domain", required=True, help="Path to the domain file.")
    parser.add_argument("--problem", required=True, help="Path to the problem file.")
    parser.add_argument("--plans", type=int, default=1, help="Maximum number of plans to request.")
    parser.add_argument("--timeout", type=float, default=None, help="Timeout in seconds per execution step.")
    parser.add_argument("--json-out", help="Optional path for the parsed JSON result.")
    parser.add_argument("--raw-out", help="Optional path for the raw planner stdout.")
    parser.add_argument("--keep-staging", action="store_true", help="Keep temporary generated Java files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = run_jshop2(
            args.domain,
            args.problem,
            plan_limit=args.plans,
            keep_staging=args.keep_staging,
            timeout_s=args.timeout,
        )
    except JSHOP2Error as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Domain: {result.domain_name}")
    print(f"Problem: {result.problem_name}")
    print(f"Plans found: {result.plan_count}")
    print(f"Time Used: {result.time_used_s}")
    if result.plans:
        print(f"First plan cost: {result.plans[0].cost}")
        print("First plan actions:")
        for action in result.plans[0].actions:
            print(f"  {action.raw}")

    if args.raw_out:
        raw_path = Path(args.raw_out)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(result.planner_stdout, encoding="utf-8")
        print(f"Raw stdout written to: {raw_path}")
    if args.json_out:
        json_path = write_result_json(result, args.json_out)
        print(f"JSON result written to: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
