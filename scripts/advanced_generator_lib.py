from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path


ADVANCED_CONTENT_TYPES = ("food", "medicine")
ADVANCED_DOMAIN_NAME = "ubermedics_advanced"


@dataclass(frozen=True)
class AdvancedProblem:
    name: str
    drones: int
    drone_locations: dict[str, str]
    locations: tuple[str, ...]
    depot_stock: dict[str, int]
    location_stock: dict[str, dict[str, int]]
    needs: dict[str, dict[str, int]]
    carrier_capacities: dict[str, int]
    carrier_locations: dict[str, str]


@dataclass(frozen=True)
class AdvancedRandomOptions:
    drones: int
    carriers: int
    locations: int
    max_need_per_type: int = 8
    carrier_capacities: tuple[int, ...] | None = None
    seed: int | None = None
    slack_per_content: int = 2
    problem_name: str | None = None


def _carrier_move_cost(capacity: int) -> int:
    return 50 + capacity // 10


def _validate_advanced_problem(problem: AdvancedProblem) -> None:
    if problem.drones < 1:
        raise ValueError("`drones` must be at least 1.")
    if "depot" not in problem.locations:
        raise ValueError("`locations` must include `depot`.")
    for location in problem.locations:
        if location not in problem.location_stock:
            raise ValueError(f"Missing stock declaration for location `{location}`.")
        if location != "depot" and location not in problem.needs:
            raise ValueError(f"Missing need declaration for location `{location}`.")
        for content in ADVANCED_CONTENT_TYPES:
            if content not in problem.location_stock[location]:
                raise ValueError(f"Missing stock for `{location}` and `{content}`.")
            if location != "depot" and content not in problem.needs[location]:
                raise ValueError(f"Missing need for `{location}` and `{content}`.")


def render_advanced_problem(problem: AdvancedProblem) -> str:
    _validate_advanced_problem(problem)

    lines = [f"(defproblem {problem.name} {ADVANCED_DOMAIN_NAME}", "  ("]

    for drone_name in sorted(problem.drone_locations):
        lines.append(f"    (drone {drone_name})")
    for location in problem.locations:
        lines.append(f"    (location {location})")
    for content in ADVANCED_CONTENT_TYPES:
        lines.append(f"    (content {content})")
    for carrier_name in sorted(problem.carrier_capacities):
        lines.append(f"    (carrier {carrier_name})")

    for drone_name, location in sorted(problem.drone_locations.items()):
        lines.append(f"    (drone-at {drone_name} {location})")
        lines.append(f"    (drone-free {drone_name})")

    for location in problem.locations:
        for content in ADVANCED_CONTENT_TYPES:
            quantity = problem.location_stock[location][content]
            lines.append(f"    (stock {location} {content} {quantity})")

    for location in problem.locations:
        if location == "depot":
            for content in ADVANCED_CONTENT_TYPES:
                lines.append(f"    (need depot {content} 0)")
            continue
        for content in ADVANCED_CONTENT_TYPES:
            lines.append(f"    (need {location} {content} {problem.needs[location][content]})")

    for carrier_name, capacity in sorted(problem.carrier_capacities.items()):
        location = problem.carrier_locations[carrier_name]
        lines.append(f"    (carrier-at {carrier_name} {location})")
        lines.append(f"    (carrier-capacity {carrier_name} {capacity})")
        lines.append(f"    (carrier-free {carrier_name} {capacity})")
        lines.append(f"    (carrier-move-cost {carrier_name} {_carrier_move_cost(capacity)})")
        for content in ADVANCED_CONTENT_TYPES:
            lines.append(f"    (carrier-load {carrier_name} {content} 0)")

    lines.append("  )")
    lines.append("  ((deliver-all))")
    lines.append(")")
    return "\n".join(lines) + "\n"


def write_advanced_problem(problem: AdvancedProblem, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_advanced_problem(problem), encoding="utf-8")
    return output_path


def generate_random_advanced_problem(options: AdvancedRandomOptions) -> AdvancedProblem:
    if options.drones < 1:
        raise ValueError("`drones` must be at least 1.")
    if options.carriers < 0:
        raise ValueError("`carriers` can not be negative.")
    if options.locations < 1:
        raise ValueError("`locations` must be at least 1.")
    if options.max_need_per_type < 1:
        raise ValueError("`max_need_per_type` must be at least 1.")

    rng = random.Random(options.seed)
    problem_name = options.problem_name or (
        f"advanced_problem_d{options.drones}_r{options.carriers}_l{options.locations}"
        + (f"_s{options.seed}" if options.seed is not None else "")
    )
    locations = ("depot",) + tuple(f"loc{i}" for i in range(1, options.locations + 1))
    drone_locations = {f"drone{i}": "depot" for i in range(1, options.drones + 1)}

    needs: dict[str, dict[str, int]] = {}
    total_per_content = {content: 0 for content in ADVANCED_CONTENT_TYPES}
    generated_any = False
    for location in locations[1:]:
        location_needs = {}
        for content in ADVANCED_CONTENT_TYPES:
            value = rng.randint(0, options.max_need_per_type)
            location_needs[content] = value
            total_per_content[content] += value
            generated_any = generated_any or value > 0
        needs[location] = location_needs

    if not generated_any:
        first_location = locations[1]
        needs[first_location]["food"] = 1
        total_per_content["food"] += 1

    location_stock = {location: {content: 0 for content in ADVANCED_CONTENT_TYPES} for location in locations}
    depot_stock = {}
    for content in ADVANCED_CONTENT_TYPES:
        depot_quantity = total_per_content[content] + options.slack_per_content
        depot_stock[content] = depot_quantity
        location_stock["depot"][content] = depot_quantity

    capacities = list(options.carrier_capacities or ())
    while len(capacities) < options.carriers:
        capacities.append(rng.choice((10, 20, 30, 40, 50, 60)))

    carrier_capacities = {
        f"carrier{i}": capacities[i - 1]
        for i in range(1, options.carriers + 1)
    }
    carrier_locations = {carrier: "depot" for carrier in carrier_capacities}

    return AdvancedProblem(
        name=problem_name,
        drones=options.drones,
        drone_locations=drone_locations,
        locations=locations,
        depot_stock=depot_stock,
        location_stock=location_stock,
        needs=needs,
        carrier_capacities=carrier_capacities,
        carrier_locations=carrier_locations,
    )
