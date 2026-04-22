#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from advanced_generator_lib import AdvancedRandomOptions, generate_random_advanced_problem, write_advanced_problem


def parse_capacities(raw: str | None) -> tuple[int, ...] | None:
    if raw is None:
        return None
    capacities = tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    return capacities or None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a random SHOP2 problem for the advanced emergency domain.")
    parser.add_argument("-d", "--drones", type=int, default=1, help="Number of drones. Official validation uses 1.")
    parser.add_argument("-r", "--carriers", type=int, default=1, help="Number of carriers.")
    parser.add_argument("-l", "--locations", type=int, required=True, help="Number of non-depot locations.")
    parser.add_argument("--max-need-per-type", type=int, default=8, help="Maximum need per content type and location.")
    parser.add_argument("--carrier-capacities", default=None, help="Comma-separated carrier capacities, e.g. `20,40,60`.")
    parser.add_argument("--slack-per-content", type=int, default=2, help="Extra depot stock per content above the total need.")
    parser.add_argument("-s", "--seed", type=int, default=None, help="Random seed.")
    parser.add_argument("--problem-name", default=None, help="Override the generated problem name.")
    parser.add_argument("--output", default=None, help="Output path. Defaults to `<problem_name>.jshop` in the current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    options = AdvancedRandomOptions(
        drones=args.drones,
        carriers=args.carriers,
        locations=args.locations,
        max_need_per_type=args.max_need_per_type,
        carrier_capacities=parse_capacities(args.carrier_capacities),
        seed=args.seed,
        slack_per_content=args.slack_per_content,
        problem_name=args.problem_name,
    )
    problem = generate_random_advanced_problem(options)
    output = Path(args.output) if args.output else Path.cwd() / f"{problem.name}.jshop"
    write_advanced_problem(problem, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
