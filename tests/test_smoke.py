from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from advanced_generator_lib import write_advanced_problem
from basic_generator_lib import BasicProblemOptions, write_basic_problem
from jshop_runner_lib import resolve_course_layout, run_jshop2
from scenarios_lib import build_scenario_problem, scenario_by_name, validate_scenario


class SmokeTests(unittest.TestCase):
    def test_basic_domain_smoke(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as temp_dir:
            problem_path = Path(temp_dir) / "basic_smoke.jshop"
            write_basic_problem(
                BasicProblemOptions(
                    drones=1,
                    carriers=0,
                    locations=2,
                    persons=2,
                    crates=2,
                    goals=2,
                    seed=3,
                ),
                problem_path,
            )
            result = run_jshop2(ROOT / "domains" / "basic" / "domain.jshop", problem_path, timeout_s=30)
            self.assertGreaterEqual(result.plan_count, 1)
            self.assertTrue(result.plans[0].actions)

    def test_selected_advanced_scenarios(self) -> None:
        for scenario_name in (
            "s01_no_carrier_loose",
            "s02_single_carrier",
            "s03_mixed_contents_same_carrier",
            "s04_carrier_then_loose_remainder",
            "s08_choose_largest_if_none_fit",
            "s10_serve_highest_need_first",
            "s11_multistop_without_return",
        ):
            with self.subTest(scenario=scenario_name):
                with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as temp_dir:
                    spec = scenario_by_name(scenario_name)
                    problem = build_scenario_problem(spec)
                    problem_path = Path(temp_dir) / f"{scenario_name}.jshop"
                    write_advanced_problem(problem, problem_path)
                    result = run_jshop2(ROOT / "domains" / "advanced" / "domain.jshop", problem_path, timeout_s=30)
                    self.assertEqual(validate_scenario(spec, result), [])

    def test_professor_course_layout_smoke(self) -> None:
        domain_path, problem_path = resolve_course_layout(ROOT.parent / "JSHOP2" / "domains" / "basic")
        result = run_jshop2(domain_path, problem_path, timeout_s=30)
        self.assertGreaterEqual(result.plan_count, 1)
        self.assertTrue(result.plans[0].actions)


if __name__ == "__main__":
    unittest.main(verbosity=2)
