from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from advanced_generator_lib import AdvancedProblem, write_advanced_problem
from jshop_runner_lib import Action, RunResult, write_result_json


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    description: str
    locations: tuple[str, ...]
    needs: dict[str, dict[str, int]]
    depot_stock: dict[str, int]
    carrier_capacities: tuple[int, ...]
    drones: int = 1
    expected_first_delivery: str | None = None
    expected_carrier_sequence: tuple[str, ...] = ()
    expected_first_trip_carrier: str | None = None
    expected_first_trip_total_load: int | None = None
    require_carrier: bool = False
    require_loose: bool = False
    require_mixed_first_trip: bool = False
    require_multistop: bool = False


def _zero_stocks(locations: tuple[str, ...]) -> dict[str, dict[str, int]]:
    return {location: {"food": 0, "medicine": 0} for location in locations}


def build_scenario_problem(spec: ScenarioSpec) -> AdvancedProblem:
    locations = ("depot",) + spec.locations
    location_stock = _zero_stocks(locations)
    location_stock["depot"] = {
        "food": spec.depot_stock["food"],
        "medicine": spec.depot_stock["medicine"],
    }
    carrier_capacities = {
        f"carrier{i}": capacity
        for i, capacity in enumerate(spec.carrier_capacities, start=1)
    }
    return AdvancedProblem(
        name=spec.name,
        drones=spec.drones,
        drone_locations={f"drone{i}": "depot" for i in range(1, spec.drones + 1)},
        locations=locations,
        depot_stock=spec.depot_stock,
        location_stock=location_stock,
        needs=spec.needs,
        carrier_capacities=carrier_capacities,
        carrier_locations={carrier: "depot" for carrier in carrier_capacities},
    )


SCENARIOS: tuple[ScenarioSpec, ...] = (
    ScenarioSpec(
        name="s01_no_carrier_loose",
        description="No transporters available, so the drone must deliver loose boxes.",
        locations=("loc1",),
        needs={"loc1": {"food": 2, "medicine": 1}},
        depot_stock={"food": 2, "medicine": 1},
        carrier_capacities=(),
        expected_first_delivery="loc1",
        require_loose=True,
    ),
    ScenarioSpec(
        name="s02_single_carrier",
        description="A single carrier is available and should be used for a multi-box delivery.",
        locations=("loc1",),
        needs={"loc1": {"food": 2, "medicine": 1}},
        depot_stock={"food": 2, "medicine": 1},
        carrier_capacities=(20,),
        expected_first_delivery="loc1",
        expected_first_trip_carrier="carrier1",
        require_carrier=True,
    ),
    ScenarioSpec(
        name="s03_mixed_contents_same_carrier",
        description="Food and medicine should be loaded on the same transporter.",
        locations=("loc1",),
        needs={"loc1": {"food": 2, "medicine": 3}},
        depot_stock={"food": 2, "medicine": 3},
        carrier_capacities=(20,),
        expected_first_delivery="loc1",
        expected_first_trip_carrier="carrier1",
        require_carrier=True,
        require_mixed_first_trip=True,
    ),
    ScenarioSpec(
        name="s04_carrier_then_loose_remainder",
        description="A carrier covers most of the need, then the last box is delivered loose.",
        locations=("loc1",),
        needs={"loc1": {"food": 3, "medicine": 2}},
        depot_stock={"food": 3, "medicine": 2},
        carrier_capacities=(4,),
        expected_first_delivery="loc1",
        expected_first_trip_carrier="carrier1",
        require_carrier=True,
        require_loose=True,
    ),
    ScenarioSpec(
        name="s05_small_carrier_loads_max",
        description="An insufficient carrier should be loaded to full capacity.",
        locations=("loc1",),
        needs={"loc1": {"food": 4, "medicine": 2}},
        depot_stock={"food": 4, "medicine": 2},
        carrier_capacities=(3,),
        expected_first_delivery="loc1",
        expected_first_trip_carrier="carrier1",
        expected_first_trip_total_load=3,
        require_carrier=True,
    ),
    ScenarioSpec(
        name="s06_large_carrier_loads_partial",
        description="A large transporter should load only what the destination needs.",
        locations=("loc1",),
        needs={"loc1": {"food": 3, "medicine": 1}},
        depot_stock={"food": 3, "medicine": 1},
        carrier_capacities=(20,),
        expected_first_delivery="loc1",
        expected_first_trip_carrier="carrier1",
        expected_first_trip_total_load=4,
        require_carrier=True,
    ),
    ScenarioSpec(
        name="s07_choose_smallest_fitting",
        description="If several carriers fit, choose the smallest sufficient one.",
        locations=("loc1",),
        needs={"loc1": {"food": 10, "medicine": 8}},
        depot_stock={"food": 10, "medicine": 8},
        carrier_capacities=(20, 40, 60),
        expected_first_delivery="loc1",
        expected_first_trip_carrier="carrier1",
        require_carrier=True,
    ),
    ScenarioSpec(
        name="s08_choose_largest_if_none_fit",
        description="If no carrier is large enough, choose the largest one.",
        locations=("loc1",),
        needs={"loc1": {"food": 20, "medicine": 15}},
        depot_stock={"food": 20, "medicine": 15},
        carrier_capacities=(10, 20, 30),
        expected_first_delivery="loc1",
        expected_first_trip_carrier="carrier3",
        require_carrier=True,
    ),
    ScenarioSpec(
        name="s09_reselect_after_return",
        description="After returning to the depot, the next transporter should reflect updated needs.",
        locations=("loc1", "loc2"),
        needs={
            "loc1": {"food": 20, "medicine": 15},
            "loc2": {"food": 10, "medicine": 5},
        },
        depot_stock={"food": 30, "medicine": 20},
        carrier_capacities=(20, 40),
        expected_first_delivery="loc1",
        expected_carrier_sequence=("carrier2", "carrier1"),
        require_carrier=True,
    ),
    ScenarioSpec(
        name="s10_serve_highest_need_first",
        description="The first location served must be the one with greatest total need.",
        locations=("loc1", "loc2", "loc3"),
        needs={
            "loc1": {"food": 4, "medicine": 2},
            "loc2": {"food": 6, "medicine": 4},
            "loc3": {"food": 2, "medicine": 2},
        },
        depot_stock={"food": 12, "medicine": 8},
        carrier_capacities=(10,),
        expected_first_delivery="loc2",
        expected_first_trip_carrier="carrier1",
        require_carrier=True,
    ),
    ScenarioSpec(
        name="s11_multistop_without_return",
        description="A single carrier trip should satisfy more than one location before returning.",
        locations=("loc1", "loc2", "loc3"),
        needs={
            "loc1": {"food": 6, "medicine": 4},
            "loc2": {"food": 5, "medicine": 3},
            "loc3": {"food": 4, "medicine": 5},
        },
        depot_stock={"food": 15, "medicine": 12},
        carrier_capacities=(18,),
        expected_first_delivery="loc1",
        expected_first_trip_carrier="carrier1",
        require_carrier=True,
        require_multistop=True,
    ),
    ScenarioSpec(
        name="s12_combined_regression",
        description="Combined regression: re-selection and multi-stop carrier use in one run.",
        locations=("loc1", "loc2", "loc3"),
        needs={
            "loc1": {"food": 25, "medicine": 25},
            "loc2": {"food": 7, "medicine": 5},
            "loc3": {"food": 1, "medicine": 0},
        },
        depot_stock={"food": 33, "medicine": 30},
        carrier_capacities=(12, 50),
        expected_first_delivery="loc1",
        expected_carrier_sequence=("carrier2", "carrier2"),
        require_carrier=True,
        require_multistop=True,
    ),
)


def _first_delivery_location(actions: Iterable[Action]) -> str | None:
    for action in actions:
        if action.name == "!deliver-from-carrier":
            return action.args[2]
        if action.name == "!deliver-loose":
            return action.args[1]
    return None


def _carrier_trip_sequence(actions: list[Action]) -> list[str]:
    sequence: list[str] = []
    for action in actions:
        if action.name == "!fly-with-carrier" and len(action.args) == 4 and action.args[2] == "depot":
            sequence.append(action.args[1])
    return sequence


def _first_trip_load(actions: list[Action]) -> tuple[str | None, int, set[str]]:
    carrier_name: str | None = None
    total = 0
    contents: set[str] = set()
    for action in actions:
        if action.name == "!load-carrier":
            carrier_name = action.args[1]
            contents.add(action.args[2])
            total += int(float(action.args[3]))
            continue
        if action.name == "!fly-with-carrier":
            break
    return carrier_name, total, contents


def _has_multistop_trip(actions: list[Action]) -> bool:
    active_locations: list[str] = []
    in_trip = False
    for action in actions:
        if action.name == "!fly-with-carrier" and action.args[2] == "depot":
            in_trip = True
            active_locations = []
            continue
        if in_trip and action.name == "!deliver-from-carrier":
            active_locations.append(action.args[2])
            continue
        if in_trip and action.name == "!fly-with-carrier" and action.args[3] == "depot":
            if len(dict.fromkeys(active_locations)) >= 2:
                return True
            in_trip = False
    return False


def validate_scenario(spec: ScenarioSpec, result: RunResult) -> list[str]:
    if result.plan_count < 1 or not result.plans:
        return ["JSHOP2 did not return any valid plan."]

    errors: list[str] = []
    actions = list(result.plans[0].actions)
    names = {action.name for action in actions}

    if spec.require_carrier and "!fly-with-carrier" not in names:
        errors.append("Expected at least one carrier trip, but none was found.")
    if spec.require_loose and "!deliver-loose" not in names:
        errors.append("Expected at least one loose delivery, but none was found.")

    first_delivery = _first_delivery_location(actions)
    if spec.expected_first_delivery and first_delivery != spec.expected_first_delivery:
        errors.append(
            f"Expected first delivery at `{spec.expected_first_delivery}`, got `{first_delivery}`."
        )

    if spec.expected_carrier_sequence:
        actual_sequence = tuple(_carrier_trip_sequence(actions))
        if actual_sequence[: len(spec.expected_carrier_sequence)] != spec.expected_carrier_sequence:
            errors.append(
                "Unexpected carrier sequence: "
                f"expected {list(spec.expected_carrier_sequence)}, got {list(actual_sequence)}."
            )

    first_trip_carrier, first_trip_total, first_trip_contents = _first_trip_load(actions)
    if spec.expected_first_trip_carrier and first_trip_carrier != spec.expected_first_trip_carrier:
        errors.append(
            f"Expected first trip carrier `{spec.expected_first_trip_carrier}`, "
            f"got `{first_trip_carrier}`."
        )
    if spec.expected_first_trip_total_load is not None and first_trip_total != spec.expected_first_trip_total_load:
        errors.append(
            f"Expected first trip load {spec.expected_first_trip_total_load}, got {first_trip_total}."
        )
    if spec.require_mixed_first_trip and first_trip_contents != {"food", "medicine"}:
        errors.append(
            f"Expected mixed contents on the first trip, got {sorted(first_trip_contents)}."
        )
    if spec.require_multistop and not _has_multistop_trip(actions):
        errors.append("Expected a multi-stop carrier trip before returning to the depot.")

    return errors


def scenario_by_name(name: str) -> ScenarioSpec:
    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario
    raise KeyError(f"Unknown scenario `{name}`.")


def write_scenario_bundle(
    spec: ScenarioSpec,
    problem: AdvancedProblem,
    result: RunResult,
    *,
    output_dir: str | Path,
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    problem_path = output_dir / f"{spec.name}.problem.jshop"
    raw_path = output_dir / f"{spec.name}.stdout.txt"
    json_path = output_dir / f"{spec.name}.result.json"

    write_advanced_problem(problem, problem_path)
    raw_path.write_text(result.planner_stdout, encoding="utf-8")
    write_result_json(result, json_path)
    return {"problem": problem_path, "raw": raw_path, "json": json_path}
