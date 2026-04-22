from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DOMAIN_NAME_RE = re.compile(r"\(defdomain\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
PROBLEM_NAME_RE = re.compile(r"\(defproblem\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
PLAN_COUNT_RE = re.compile(r"(\d+)\s+plan\(s\)\s+were\s+found:", re.IGNORECASE)
PLAN_BLOCK_RE = re.compile(
    r"Plan\s+#(?P<index>\d+):\s*Plan cost:\s*(?P<cost>[0-9.]+)\s*(?P<body>.*?)-{5,}",
    re.IGNORECASE | re.DOTALL,
)
TIME_USED_RE = re.compile(r"Time Used\s*=\s*([0-9.]+)")


class JSHOP2Error(RuntimeError):
    pass


@dataclass(frozen=True)
class Action:
    name: str
    args: tuple[str, ...]
    raw: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "args": list(self.args), "raw": self.raw}


@dataclass(frozen=True)
class Plan:
    index: int
    cost: float
    actions: tuple[Action, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "cost": self.cost,
            "actions": [action.to_dict() for action in self.actions],
        }


@dataclass(frozen=True)
class RunResult:
    domain_name: str
    problem_name: str
    staging_dir: str
    compile_stdout: str
    compile_stderr: str
    problem_compile_stdout: str
    problem_compile_stderr: str
    javac_stdout: str
    javac_stderr: str
    planner_stdout: str
    planner_stderr: str
    plan_count: int
    time_used_s: float | None
    plans: tuple[Plan, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_name": self.domain_name,
            "problem_name": self.problem_name,
            "staging_dir": self.staging_dir,
            "compile_stdout": self.compile_stdout,
            "compile_stderr": self.compile_stderr,
            "problem_compile_stdout": self.problem_compile_stdout,
            "problem_compile_stderr": self.problem_compile_stderr,
            "javac_stdout": self.javac_stdout,
            "javac_stderr": self.javac_stderr,
            "planner_stdout": self.planner_stdout,
            "planner_stderr": self.planner_stderr,
            "plan_count": self.plan_count,
            "time_used_s": self.time_used_s,
            "plans": [plan.to_dict() for plan in self.plans],
        }


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def cache_root() -> Path:
    root = repo_root() / ".cache" / "jshop2"
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_course_layout(domain_dir: str | Path) -> tuple[Path, Path]:
    domain_dir = Path(domain_dir).resolve()
    if not domain_dir.exists():
        raise JSHOP2Error(f"Course layout directory does not exist: {domain_dir}")
    if not domain_dir.is_dir():
        raise JSHOP2Error(f"Course layout path is not a directory: {domain_dir}")

    domain_file = domain_dir / domain_dir.name
    problem_file = domain_dir / "problem"
    missing = [str(path) for path in (domain_file, problem_file) if not path.exists()]
    if missing:
        raise JSHOP2Error(
            "Invalid course layout. Expected an extensionless domain file matching the "
            f"directory name and a `problem` file inside `{domain_dir}`. Missing: {', '.join(missing)}"
        )
    return domain_file, problem_file


def parse_domain_name(domain_text: str) -> str:
    match = DOMAIN_NAME_RE.search(domain_text)
    if not match:
        raise JSHOP2Error("Could not find a valid `(defdomain ...)` declaration.")
    return match.group(1)


def parse_problem_name(problem_text: str) -> str:
    match = PROBLEM_NAME_RE.search(problem_text)
    if not match:
        raise JSHOP2Error("Could not find a valid `(defproblem ...)` declaration.")
    return match.group(1)


def build_classpath() -> str:
    root = repo_root()
    antlr_jar = root / "vendor" / "jshop2" / "console" / "antlr.jar"
    jshop_jar = root / "vendor" / "jshop2" / "console" / "JSHOP2.jar"
    missing = [str(path) for path in (antlr_jar, jshop_jar) if not path.exists()]
    if missing:
        raise JSHOP2Error(f"Missing JSHOP2 runtime files: {', '.join(missing)}")
    return os.pathsep.join([".", str(antlr_jar), str(jshop_jar)])


def parse_action(line: str) -> Action:
    text = line.strip()
    if not text.startswith("(") or not text.endswith(")"):
        raise JSHOP2Error(f"Unexpected action line: {line}")
    tokens = text[1:-1].split()
    if not tokens:
        raise JSHOP2Error(f"Empty action line: {line}")
    return Action(name=tokens[0], args=tuple(tokens[1:]), raw=text)


def parse_planner_stdout(stdout: str) -> tuple[int, float | None, tuple[Plan, ...]]:
    plan_count_match = PLAN_COUNT_RE.search(stdout)
    plan_count = int(plan_count_match.group(1)) if plan_count_match else 0

    plans: list[Plan] = []
    for match in PLAN_BLOCK_RE.finditer(stdout):
        action_lines = [
            line.strip()
            for line in match.group("body").splitlines()
            if line.strip().startswith("(")
        ]
        actions = tuple(parse_action(line) for line in action_lines)
        plans.append(
            Plan(
                index=int(match.group("index")),
                cost=float(match.group("cost")),
                actions=actions,
            )
        )

    time_used_match = TIME_USED_RE.search(stdout)
    time_used = float(time_used_match.group(1)) if time_used_match else None
    return plan_count, time_used, tuple(plans)


def _run_command(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    label: str,
    timeout_s: float | None,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise JSHOP2Error(
            f"{label} timed out after {timeout_s}s.\n"
            f"STDOUT:\n{exc.stdout or ''}\n"
            f"STDERR:\n{exc.stderr or ''}"
        ) from exc
    if completed.returncode != 0:
        raise JSHOP2Error(
            f"{label} failed with exit code {completed.returncode}.\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}"
        )
    return completed


def run_jshop2(
    domain_path: str | Path,
    problem_path: str | Path,
    *,
    plan_limit: int = 1,
    keep_staging: bool = False,
    timeout_s: float | None = None,
) -> RunResult:
    domain_path = Path(domain_path).resolve()
    problem_path = Path(problem_path).resolve()

    domain_text = domain_path.read_text(encoding="utf-8")
    problem_text = problem_path.read_text(encoding="utf-8")

    domain_name = parse_domain_name(domain_text)
    problem_name = parse_problem_name(problem_text)

    staging_dir = Path(tempfile.mkdtemp(prefix=f"{domain_name}_", dir=cache_root()))
    try:
        (staging_dir / domain_name).write_text(domain_text, encoding="utf-8")
        (staging_dir / "problem").write_text(problem_text, encoding="utf-8")

        env = os.environ.copy()
        env["CLASSPATH"] = build_classpath()

        compile_domain = _run_command(
            ["java", "JSHOP2.InternalDomain", domain_name],
            cwd=staging_dir,
            env=env,
            label="Domain compilation",
            timeout_s=timeout_s,
        )
        compile_problem = _run_command(
            ["java", "JSHOP2.InternalDomain", f"-r{plan_limit}", "problem"],
            cwd=staging_dir,
            env=env,
            label="Problem compilation",
            timeout_s=timeout_s,
        )
        javac_compile = _run_command(
            ["javac", f"{domain_name}.java", f"{problem_name}.java"],
            cwd=staging_dir,
            env=env,
            label="Java compilation",
            timeout_s=timeout_s,
        )
        planner_run = _run_command(
            ["java", problem_name],
            cwd=staging_dir,
            env=env,
            label="Planner execution",
            timeout_s=timeout_s,
        )

        plan_count, time_used_s, plans = parse_planner_stdout(planner_run.stdout)
        return RunResult(
            domain_name=domain_name,
            problem_name=problem_name,
            staging_dir=str(staging_dir),
            compile_stdout=compile_domain.stdout,
            compile_stderr=compile_domain.stderr,
            problem_compile_stdout=compile_problem.stdout,
            problem_compile_stderr=compile_problem.stderr,
            javac_stdout=javac_compile.stdout,
            javac_stderr=javac_compile.stderr,
            planner_stdout=planner_run.stdout,
            planner_stderr=planner_run.stderr,
            plan_count=plan_count,
            time_used_s=time_used_s,
            plans=plans,
        )
    finally:
        if not keep_staging:
            shutil.rmtree(staging_dir, ignore_errors=True)


def write_result_json(result: RunResult, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path
