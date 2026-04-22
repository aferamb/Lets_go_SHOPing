from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path


BASIC_CONTENT_TYPES = ("food", "medicine")
BASIC_DOMAIN_NAME = "ubermedics_basic"


@dataclass(frozen=True)
class BasicProblemOptions:
    drones: int
    carriers: int
    locations: int
    persons: int
    crates: int
    goals: int
    seed: int | None = None
    problem_name: str | None = None


def _validate_basic_options(options: BasicProblemOptions) -> None:
    if options.drones < 1:
        raise ValueError("`drones` must be at least 1.")
    if options.carriers < 0:
        raise ValueError("`carriers` can not be negative.")
    if options.locations < 1:
        raise ValueError("`locations` must be at least 1.")
    if options.persons < 1:
        raise ValueError("`persons` must be at least 1.")
    if options.crates < 1:
        raise ValueError("`crates` must be at least 1.")
    if options.goals < 1:
        raise ValueError("`goals` must be at least 1.")
    if options.goals > options.crates:
        raise ValueError("Can not have more goals than crates.")
    if options.goals > len(BASIC_CONTENT_TYPES) * options.persons:
        raise ValueError("Too many goals for the number of persons and content types.")


def _setup_content_types(rng: random.Random, options: BasicProblemOptions) -> list[list[str]]:
    while True:
        per_content: list[int] = []
        crates_left = options.crates
        for index in range(len(BASIC_CONTENT_TYPES) - 1):
            types_after = len(BASIC_CONTENT_TYPES) - index - 1
            max_now = crates_left - types_after
            value = rng.randint(1, max_now)
            per_content.append(value)
            crates_left -= value
        per_content.append(crates_left)

        max_goals = sum(min(num, options.persons) for num in per_content)
        if options.goals <= max_goals:
            break

    crates_with_content: list[list[str]] = []
    counter = 1
    for amount in per_content:
        names = []
        for _ in range(amount):
            names.append(f"crate{counter}")
            counter += 1
        crates_with_content.append(names)
    return crates_with_content


def _setup_person_needs(
    rng: random.Random,
    options: BasicProblemOptions,
    crates_with_content: list[list[str]],
) -> list[list[bool]]:
    need = [[False for _ in BASIC_CONTENT_TYPES] for _ in range(options.persons)]
    goals_per_content = [0 for _ in BASIC_CONTENT_TYPES]

    for _ in range(options.goals):
        generated = False
        while not generated:
            person_index = rng.randint(0, options.persons - 1)
            content_index = rng.randint(0, len(BASIC_CONTENT_TYPES) - 1)
            if (
                goals_per_content[content_index] < len(crates_with_content[content_index])
                and not need[person_index][content_index]
            ):
                need[person_index][content_index] = True
                goals_per_content[content_index] += 1
                generated = True
    return need


def _problem_name(options: BasicProblemOptions) -> str:
    if options.problem_name:
        return options.problem_name
    return (
        f"drone_problem_basic_d{options.drones}_r{options.carriers}_l{options.locations}"
        f"_p{options.persons}_c{options.crates}_g{options.goals}_ct{len(BASIC_CONTENT_TYPES)}"
        + (f"_s{options.seed}" if options.seed is not None else "")
    )


def render_basic_problem(options: BasicProblemOptions) -> str:
    _validate_basic_options(options)
    rng = random.Random(options.seed)

    problem_name = _problem_name(options)
    drones = [f"drone{i}" for i in range(1, options.drones + 1)]
    locations = ["depot"] + [f"loc{i}" for i in range(1, options.locations + 1)]
    persons = [f"person{i}" for i in range(1, options.persons + 1)]
    crates = [f"crate{i}" for i in range(1, options.crates + 1)]

    crates_with_content = _setup_content_types(rng, options)
    needs = _setup_person_needs(rng, options, crates_with_content)
    person_locations = {
        person: locations[rng.randint(1, len(locations) - 1)]
        for person in persons
    }

    lines = [f"(defproblem {problem_name} {BASIC_DOMAIN_NAME}", "  ("]
    for drone in drones:
        lines.append(f"    (drone {drone})")
    for location in locations:
        lines.append(f"    (location {location})")
    for crate in crates:
        lines.append(f"    (crate {crate})")
    for content in BASIC_CONTENT_TYPES:
        lines.append(f"    (content {content})")
    for person in persons:
        lines.append(f"    (person {person})")

    for drone in drones:
        lines.append(f"    (drone-at {drone} depot)")
        lines.append(f"    (arm-free-left {drone})")
        lines.append(f"    (arm-free-right {drone})")

    for crate in crates:
        lines.append(f"    (crate-at {crate} depot)")

    for content, crate_names in zip(BASIC_CONTENT_TYPES, crates_with_content, strict=True):
        for crate in crate_names:
            lines.append(f"    (crate-has {crate} {content})")

    for person in persons:
        lines.append(f"    (person-at {person} {person_locations[person]})")

    for person_index, person in enumerate(persons):
        for content_index, content in enumerate(BASIC_CONTENT_TYPES):
            if needs[person_index][content_index]:
                lines.append(f"    (need {person} {content})")

    lines.append("  )")
    lines.append("  ((deliver-all))")
    lines.append(")")
    return "\n".join(lines) + "\n"


def generate_basic_problem(options: BasicProblemOptions) -> tuple[str, str]:
    name = _problem_name(options)
    return name, render_basic_problem(options)


def write_basic_problem(options: BasicProblemOptions, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_basic_problem(options), encoding="utf-8")
    return output_path
