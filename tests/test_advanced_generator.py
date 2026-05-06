from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from advanced_generator_lib import AdvancedProblem, render_advanced_problem, write_advanced_problem
from jshop_runner_lib import run_jshop2
from scenarios_lib import build_scenario_problem, scenario_by_name


class AdvancedGeneratorTests(unittest.TestCase):
    def test_render_advanced_problem_keeps_exact_carrier_move_cost(self) -> None:
        problem = AdvancedProblem(
            name="advanced_cost_render",
            drones=1,
            drone_locations={"drone1": "depot"},
            locations=("depot", "loc1"),
            depot_stock={"food": 1, "medicine": 0},
            location_stock={
                "depot": {"food": 1, "medicine": 0},
                "loc1": {"food": 0, "medicine": 0},
            },
            needs={"loc1": {"food": 1, "medicine": 0}},
            carrier_capacities={"carrier1": 4, "carrier2": 20},
            carrier_locations={"carrier1": "depot", "carrier2": "depot"},
        )

        rendered = render_advanced_problem(problem)

        self.assertIn("(carrier-move-cost carrier1 50.4)", rendered)
        self.assertIn("(carrier-move-cost carrier2 52)", rendered)

    def test_non_multiple_of_ten_carrier_changes_plan_cost(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as temp_dir:
            spec = scenario_by_name("s04_carrier_then_loose_remainder")
            problem = build_scenario_problem(spec)
            problem_path = Path(temp_dir) / f"{spec.name}.jshop"

            write_advanced_problem(problem, problem_path)
            result = run_jshop2(ROOT / "domains" / "advanced" / "domain.jshop", problem_path, timeout_s=30)

            self.assertGreaterEqual(result.plan_count, 1)
            self.assertTrue(result.plans)
            self.assertAlmostEqual(result.plans[0].cost, 200.8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
