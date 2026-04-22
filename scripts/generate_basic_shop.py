#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from basic_generator_lib import BasicProblemOptions, generate_basic_problem, write_basic_problem


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a SHOP2 problem for the basic emergency domain.")
    parser.add_argument("-d", "--drones", type=int, required=True, help="Number of drones.")
    parser.add_argument("-r", "--carriers", type=int, default=0, help="Compatibility flag from PL1; ignored by the basic domain.")
    parser.add_argument("-l", "--locations", type=int, required=True, help="Number of locations apart from the depot.")
    parser.add_argument("-p", "--persons", type=int, required=True, help="Number of persons.")
    parser.add_argument("-c", "--crates", type=int, required=True, help="Number of crates.")
    parser.add_argument("-g", "--goals", type=int, required=True, help="Number of needs to generate.")
    parser.add_argument("-s", "--seed", type=int, default=None, help="Random seed.")
    parser.add_argument("--problem-name", default=None, help="Override the generated problem name.")
    parser.add_argument("--output", default=None, help="Output path. Defaults to `<problem_name>.jshop` in the current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    options = BasicProblemOptions(
        drones=args.drones,
        carriers=args.carriers,
        locations=args.locations,
        persons=args.persons,
        crates=args.crates,
        goals=args.goals,
        seed=args.seed,
        problem_name=args.problem_name,
    )

    name, _ = generate_basic_problem(options)
    output = Path(args.output) if args.output else Path.cwd() / f"{name}.jshop"
    write_basic_problem(options, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
