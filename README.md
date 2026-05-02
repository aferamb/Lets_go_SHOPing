# Lets_go_SHOPing

Standalone SHOP2/JSHOP2 implementation for the PL2 hierarchical planning practice.

This repository implements both practice parts:

- `domains/basic/domain.jshop`: exercise 1.1, based on the PL1 emergency-delivery problem.
- `domains/advanced/domain.jshop`: exercise 1.2, with numeric needs, depot stock, carriers, and deterministic HTN policies.

The repository was reviewed against the course bundle in `PL2/JSHOP2`, especially:

- `PL2/JSHOP2/LEEME.txt`
- `PL2/JSHOP2/domains/basic/basic`
- `PL2/JSHOP2/domains/blocks/blocks`
- `PL2/JSHOP2/domains/logistics/logistics`

## Requirements

- Python 3.10+
- Java 17+

No external Python dependency is required. If `matplotlib` is installed, the basic benchmark also produces a PNG chart.

## Repository Layout

- `domains/basic/domain.jshop`: basic HTN domain for exercise 1.1.
- `domains/advanced/domain.jshop`: advanced HTN domain for exercise 1.2.
- `scripts/run_jshop2.py`: general runner for any domain and problem paths.
- `scripts/run_course_layout.py`: compatibility runner for the professor-style fixed layout.
- `scripts/generate_basic_shop.py`: random generator for the basic domain.
- `scripts/generate_advanced_shop.py`: random generator for the advanced domain.
- `scripts/benchmark_basic.py`: size sweep for exercise 1.1 plus baseline comparison against PL1 exercise 1.2.
- `scripts/export_pl1_ff_baseline.py`: normalize a PL1 FF benchmark CSV into the vendored baseline format used here.
- `scripts/run_scenarios.py`: deterministic regression suite for exercise 1.2.
- `scripts/jshop_runner_lib.py`: reusable JSHOP2 execution and parsing logic.
- `scripts/basic_generator_lib.py`: reusable basic problem generator.
- `scripts/advanced_generator_lib.py`: reusable advanced problem generator.
- `scripts/scenarios_lib.py`: reusable advanced scenario definitions and validators.
- `references/pl1_part1_ex12_ff_baseline.csv`: vendored baseline from PL1 part 1 exercise 1.2 (FF benchmark).
- `references/pl1_part1_bfs_baseline.csv`: legacy BFS baseline kept only for backward-compatible manual runs.
- `vendor/jshop2/console/`: vendored JSHOP2 console runtime.

## Python Module Policy

The Python support code is intentionally not exposed as an installable package anymore.

- Reusable code lives as plain modules inside `scripts/`.
- CLI scripts import sibling modules such as `jshop_runner_lib` or `basic_generator_lib`.
- Tests also import from `scripts/` by adding that directory to `sys.path`.
- There is no required `import shoping` workflow.

This choice keeps the repository closer to a self-contained coursework project: executable scripts first, reusable helpers second, package installation never required.

## Recommended Workflow

Generate and solve one basic problem:

```bash
python3 scripts/generate_basic_shop.py -d 1 -r 0 -l 3 -p 3 -c 3 -g 3 --seed 7 --output .cache/basic_demo.jshop
python3 scripts/run_jshop2.py --domain domains/basic/domain.jshop --problem .cache/basic_demo.jshop --json-out .cache/basic_demo.json
```

Generate and solve one advanced problem:

```bash
python3 scripts/generate_advanced_shop.py -d 1 -r 2 -l 3 --carrier-capacities 20,40 --seed 11 --output .cache/advanced_demo.jshop
python3 scripts/run_jshop2.py --domain domains/advanced/domain.jshop --problem .cache/advanced_demo.jshop
```

Run the advanced validation suite:

```bash
python3 scripts/run_scenarios.py --suite advanced --results-dir .cache/scenarios_full
```

Run the basic benchmark:

```bash
python3 scripts/benchmark_basic.py --min-size 2 --max-size 6 --step 1 --results-dir .cache/bench_basic
```

By default, this benchmark compares SHOP2 against the vendored **PL1 part 1 exercise 1.2 FF baseline** in `references/pl1_part1_ex12_ff_baseline.csv`.

## Course-Compatible Workflow

`PL2/JSHOP2/LEEME.txt` describes a fixed layout:

- each domain lives in `domains/<name>/`
- the domain file is extensionless and must be named exactly like the folder
- the problem file must be named `problem`
- the shell scripts then run JSHOP2 inside that directory

This repository supports that layout through:

```bash
python3 scripts/run_course_layout.py --domain-dir ../JSHOP2/domains/basic
```

That compatibility runner:

- locates `<domain-dir>/<folder-name>` and `<domain-dir>/problem`
- runs the same staged JSHOP2 pipeline used everywhere else in this repository
- preserves the JSON and raw-output options from the general runner

If you want the original course GUI flow, use the professor bundle directly:

```bash
cd ../JSHOP2
./jshop2-gui.sh basic
```

## Comparison with `PL2/JSHOP2`

| Topic | Professor bundle | This repository | Why this implementation differs |
| --- | --- | --- | --- |
| Launcher | Shell scripts: `jshop2-console.sh`, `jshop2-gui.sh` | Python scripts: `run_jshop2.py`, `run_course_layout.py` | The practice needs generators, regression checks, structured outputs, and benchmark automation. |
| Input layout | Fixed: `domains/<name>/<name>` and `domains/<name>/problem` | Flexible paths, plus optional compatibility mode | Fixed names are a wrapper convention from the bundle, not a JSHOP2 language requirement. |
| Generated artifacts | JSHOP2 writes `.java`, `.txt`, and `.class` in the domain folder, then the shell script deletes them | The runner stages every run in `.cache/jshop2/...` | Staging avoids polluting tracked folders and makes repeated scripted runs safe. |
| Output format | Console text or GUI visualization | Console text, parsed JSON, raw stdout capture, scenario summaries, benchmark tables | The practice needs machine-checkable validation and reproducible reports. |
| Example scope | Teaching examples with minimal domains | Full coursework implementation with generators and tests | This repository is meant to solve the assigned exercises, not only illustrate syntax. |
| GUI support | Included | Not included | The project is centered on reproducible console runs. GUI parity is not required for the coursework deliverable. |

## Why the Domains Are More Advanced Than the Examples

The professor bundle includes examples for learning JSHOP2 syntax and idioms, not a full solution template for this practice.

- `domains/basic/basic` is a tiny syntax example with two operators and one method.
- `domains/blocks/blocks` shows axioms, bookkeeping operators such as `!!assert`, and hierarchical state-management patterns.
- `domains/logistics/logistics` shows richer transport decomposition, `:immediate`, `:protection`, axioms, and `:unordered` goals.

The current implementation reuses those ideas where they are useful, but it does not try to copy the examples literally.

### Basic domain

- The PL2 basic solution models the actual emergency-delivery exercise, not the toy `basic` example.
- It uses `:first` in `(deliver-all)` to make the policy deterministic and easy to benchmark.
- It keeps separate pickup and delivery operators for the left and right arms because that matches the original PL1 state model.

### Advanced domain

- The advanced practice needs numeric quantities for stock, needs, free carrier capacity, and carrier load.
- For that reason the domain uses `call`, `assign`, arithmetic comparisons, and `:sort-by`.
- The domain also uses `:immediate` in the transport routes, similar in spirit to the logistics example.
- It uses axioms such as `pending-location`, `has-sufficient-carrier`, and `smaller-sufficient-carrier` to support carrier selection.

These constructs make the domain look more complex than the course examples because the problem itself is more constrained:

- locations must be prioritized by total need
- carriers must be selected by capacity rules
- partial loads must respect both content types
- the execution must stay deterministic enough for scenario validation

## Why Some Course Features Are Not Used in the Same Way

- `:protection` is used heavily in the professor logistics example to preserve resource facts during decompositions. This repository does not rely on it because the delivery policy is intentionally sequential and deterministic, with one active delivery route at a time.
- `:unordered` appears in the professor logistics problem because the example starts from a goal set. This repository encodes a root task `((deliver-all))` and lets the HTN policy decide the order explicitly.
- `!!assert` and related bookkeeping operators appear in the professor blocks example. The current domains instead keep the necessary bookkeeping directly in ordinary facts and axioms because that fits the practice models more naturally.

In short, the implementation is different because the coursework asks for a deliverable planner with generators, validation, and deterministic policies, while the bundled examples are primarily teaching material.

## Validation Commands

Run the smoke tests:

```bash
python3 -m unittest tests.test_smoke -v
```

Compile-check the Python files:

```bash
python3 -m compileall scripts tests
```

Run the full advanced suite:

```bash
python3 scripts/run_scenarios.py --suite advanced --results-dir .cache/scenarios_full
```

Run the short benchmark used in the report:

```bash
python3 scripts/benchmark_basic.py --min-size 2 --max-size 6 --step 1 --results-dir .cache/bench_basic
```

Regenerate the vendored PL1 FF baseline from the PL1 repository:

```bash
python3 scripts/export_pl1_ff_baseline.py
```

`benchmark_basic.py` accepts three baseline formats through `--baseline`:

- normalized FF baselines with `ff_time_s` and `plan_length`
- raw PL1 `benchmark_ff_*.csv` files with `ff_time_s` and `plan_steps`
- the legacy BFS CSV with `search_time_s`

## Notes

- Official validation for the advanced domain is done with one drone.
- The generators still accept multiple drones for exploratory use, but the HTN policy is intentionally monodrone and deterministic.
- The advanced policy serves the highest-need location first and only adds extra full stops that fit in the remaining carrier capacity.
