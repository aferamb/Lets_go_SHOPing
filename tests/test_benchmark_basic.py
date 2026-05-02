from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from benchmark_basic import load_baseline
from export_pl1_ff_baseline import export_baseline


class BaselineLoaderTests(unittest.TestCase):
    def test_load_baseline_raw_ff_csv(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as temp_dir:
            baseline_path = Path(temp_dir) / "ff_raw.csv"
            baseline_path.write_text(
                "\n".join(
                    [
                        "size,status,solved,ff_time_s,wall_time_s,plan_steps,solver_backend,error_excerpt,problem_file",
                        "2,solved,yes,0.12,0.9500,7,planutils,,problem_2.pddl",
                        "3,timeout,no,,70.0000,,planutils,,problem_3.pddl",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            baseline = load_baseline(baseline_path)

            self.assertTrue(baseline.exists)
            self.assertEqual(baseline.label, "PL1 Exercise 1.2 (FF)")
            self.assertEqual(baseline.metric_name, "ff_time_s")
            self.assertAlmostEqual(baseline.rows[2].time_s or -1.0, 0.12)
            self.assertEqual(baseline.rows[2].plan_length, 7)
            self.assertIsNone(baseline.rows[3].time_s)

    def test_load_baseline_normalized_ff_csv(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as temp_dir:
            baseline_path = Path(temp_dir) / "ff_normalized.csv"
            baseline_path.write_text(
                "\n".join(
                    [
                        "size,status,ff_time_s,wall_time_s,plan_length",
                        "2,solved,0.08,0.9100,6",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            baseline = load_baseline(baseline_path)

            self.assertEqual(baseline.label, "PL1 Exercise 1.2 (FF)")
            self.assertEqual(baseline.metric_name, "ff_time_s")
            self.assertAlmostEqual(baseline.rows[2].time_s or -1.0, 0.08)
            self.assertEqual(baseline.rows[2].plan_length, 6)

    def test_load_baseline_legacy_bfs_csv(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as temp_dir:
            baseline_path = Path(temp_dir) / "bfs_legacy.csv"
            baseline_path.write_text(
                "\n".join(
                    [
                        "size,status,search_time_s,plan_length",
                        "2,solved,0.0005,6",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            baseline = load_baseline(baseline_path)

            self.assertEqual(baseline.label, "PL1 BFS baseline (legacy)")
            self.assertEqual(baseline.metric_name, "search_time_s")
            self.assertAlmostEqual(baseline.rows[2].time_s or -1.0, 0.0005)
            self.assertEqual(baseline.rows[2].plan_length, 6)


class BaselineExportTests(unittest.TestCase):
    def test_export_baseline_normalizes_plan_steps(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as temp_dir:
            source_path = Path(temp_dir) / "ff_raw.csv"
            output_path = Path(temp_dir) / "ff_normalized.csv"
            source_path.write_text(
                "\n".join(
                    [
                        "size,status,solved,ff_time_s,wall_time_s,plan_steps,solver_backend,error_excerpt,problem_file",
                        "2,solved,yes,0.00,0.9500,7,planutils,,problem_2.pddl",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            export_baseline(source_path, output_path)

            content = output_path.read_text(encoding="utf-8")
            self.assertIn("plan_length", content.splitlines()[0])
            self.assertNotIn("plan_steps", content.splitlines()[0])
            self.assertIn("2,solved,0.00,0.9500,7", content)


class BenchmarkBasicCliTests(unittest.TestCase):
    def test_benchmark_cli_accepts_raw_ff_baseline(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as temp_dir:
            baseline_path = Path(temp_dir) / "ff_raw.csv"
            results_dir = Path(temp_dir) / "results"
            baseline_path.write_text(
                "\n".join(
                    [
                        "size,status,solved,ff_time_s,wall_time_s,plan_steps,solver_backend,error_excerpt,problem_file",
                        "2,solved,yes,0.00,0.9500,7,planutils,,problem_2.pddl",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "benchmark_basic.py"),
                    "--min-size",
                    "2",
                    "--max-size",
                    "2",
                    "--step",
                    "1",
                    "--results-dir",
                    str(results_dir),
                    "--baseline",
                    str(baseline_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                timeout=120,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

            csv_text = (results_dir / "benchmark_basic.csv").read_text(encoding="utf-8")
            md_text = (results_dir / "benchmark_basic.md").read_text(encoding="utf-8")

            self.assertIn("baseline_time_s", csv_text.splitlines()[0])
            self.assertNotIn("baseline_search_time_s", csv_text.splitlines()[0])
            self.assertIn("PL1 Exercise 1.2 (FF)", md_text)
            self.assertIn("baseline_time_s", md_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
