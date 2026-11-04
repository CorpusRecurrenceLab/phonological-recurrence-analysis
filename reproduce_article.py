"""Rebuild every article-facing result from the frozen release inputs."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALID = ROOT / ".local" / "validation"
VALID.mkdir(parents=True, exist_ok=True)


def call(*parts: str) -> None:
    env = os.environ.copy()
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, *parts], cwd=ROOT, env=env, check=True)


stages = [
    ("verify", ["project.py", "verify"]),
    ("prepare", ["project.py", "prepare"]),
    ("core_analysis", ["project.py", "analyze"]),
    ("unit_tests", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("additional_sources", ["project.py", "extend"]),
    ("paired_comparison", ["project.py", "compare"]),
    ("qamats_sensitivity", ["src/analysis/qamats_sensitivity.py"]),
    ("article_inventory", ["src/analysis/article_inventory.py"]),
    ("worked_example", ["src/analysis/worked_example.py"]),
    ("representative_examples", ["src/analysis/representative_examples.py"]),
    ("figures", ["project.py", "figures"]),
    ("release_validation", ["src/analysis/validate_release.py"]),
]

completed = []
try:
    for label, command in stages:
        print(f"\n== {label} ==", flush=True)
        call(*command)
        completed.append(label)
finally:
    record = {
        "status": "PASS" if len(completed) == len(stages) else "INCOMPLETE",
        "completed_stages": completed,
        "python": sys.version,
    }
    (VALID / "reproduction.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
