"""Command-line entry point for the phonological-recurrence reproducibility package."""
from __future__ import annotations
import argparse, contextlib, hashlib, json, math, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_python() -> None:
    if sys.version_info < (3, 12):
        raise RuntimeError("Python 3.12 or newer is required")


def compare(a, b, path="$"):
    """Recursive exact/content comparison with tight floating tolerance."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            raise ValueError(f"Different keys at {path}")
        for key in a:
            compare(a[key], b[key], f"{path}.{key}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raise ValueError(f"Different lengths at {path}")
        for i, (x, y) in enumerate(zip(a, b)):
            compare(x, y, f"{path}[{i}]")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-12):
            raise ValueError(f"Different number at {path}: {a!r} != {b!r}")
    elif a != b:
        raise ValueError(f"Different content at {path}")


def run(script: Path, *args: str) -> None:
    env = os.environ.copy()
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, str(script), *map(str, args)], cwd=ROOT, env=env, check=True)


@contextlib.contextmanager
def lock():
    """Prevent simultaneous project commands without creating a tracked status file."""
    path = ROOT / ".local" / "run.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0)
        handle.write(b"0")
        handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError("Another project command is running") from exc
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def verify_manifest() -> None:
    require_python()
    manifest = json.loads((ROOT / "config" / "manifest.json").read_text(encoding="utf-8"))
    failures = []
    for rel, digest in manifest.items():
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"missing: {rel}")
        elif sha256(path) != digest:
            failures.append(f"changed: {rel}")
    if failures:
        raise ValueError("Manifest verification failed:\n" + "\n".join(failures))
    print(f"PASS manifest: {len(manifest)} frozen files")


def verify_core_regression() -> None:
    pairs = [
        ("matched.json", "matched.json"),
        ("coverage_matched_512.json", "coverage_matched_512.json"),
        ("coverage_matched_1280.json", "coverage_matched_1280.json"),
    ]
    for generated, reference in pairs:
        a = json.loads((ROOT / "results" / "analysis" / generated).read_text(encoding="utf-8"))
        b = json.loads((ROOT / "reference" / reference).read_text(encoding="utf-8"))
        compare(a, b)
    print("PASS core regression: exact outputs match frozen fixtures")


def prepare() -> None:
    run(ROOT / "src" / "prepare.py")


def analyze() -> None:
    segments = json.loads((ROOT / "results" / "corpus" / "segments.json").read_text(encoding="utf-8"))
    reference = json.loads((ROOT / "reference" / "segments.json").read_text(encoding="utf-8"))
    compare(segments, reference)
    run(ROOT / "src" / "analysis" / "run_matched.py")
    run(ROOT / "src" / "analysis" / "coverage.py")
    verify_core_regression()
    run(ROOT / "src" / "analysis" / "finish.py")
    run(ROOT / "src" / "analysis" / "verify_map.py")


def extend() -> None:
    run(ROOT / "src" / "additional_sources.py")
    run(ROOT / "src" / "analysis" / "spatial.py", "--additional")
    run(ROOT / "src" / "analysis" / "supplement.py", "--additional")


def compare_modes() -> None:
    run(ROOT / "src" / "analysis" / "compare_modes.py")
    run(ROOT / "src" / "analysis" / "validate_comparison.py")


def nakdan(action, retry_unfinished=False):
 # Candidate acquisition is isolated from the frozen study inputs.
 import shutil
 work=ROOT/'.local/nakdan';work.mkdir(parents=True,exist_ok=True)
 shutil.copytree(ROOT/'src/preparation',work/'src/preprocessing',dirs_exist_ok=True)
 shutil.copytree(ROOT/'config/preparation',work/'protocols/modern_control',dirs_exist_ok=True)
 raw=work/'data/data_raw/modern/benyehuda';raw.mkdir(parents=True,exist_ok=True)
 for ident,slug in json.loads((ROOT/'config/corpora.json').read_text(encoding='utf-8'))['modern'].items():
  shutil.copy(ROOT/f'sources/original/modern/{slug}.txt',raw/f'{ident}.txt')
 for name in ['prepare_benyehuda_control.py','prepare_nakdan_batches.py']:
  run(work/'src/preprocessing'/name)
 if action=='nakdan-prepare':run(work/'src/preprocessing/dicta_control_all.py')
 elif action=='nakdan-send':run(work/'src/preprocessing/dicta_control_all.py','--send', *(['--retry-unfinished'] if retry_unfinished else []))
 elif action=='nakdan-assemble':
  for name in ['assemble_control_review.py','prepare_control_reading.py']:run(work/'src/preprocessing'/name)
 print('Candidate workspace:',work)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=["verify", "prepare", "analyze", "core", "extend", "compare", "figures", "download", "nakdan-prepare", "nakdan-send", "nakdan-assemble"],
    )
    parser.add_argument("--cached", action="store_true", help="Use bundled originals for download verification")
    parser.add_argument("--retry-unfinished", action="store_true", help="Explicit Nakdan retry after an unresolved request")
    args = parser.parse_args()
    if args.cached and args.command != "download": parser.error("--cached applies only to download")
    if args.retry_unfinished and args.command != "nakdan-send": parser.error("--retry-unfinished applies only to nakdan-send")
    verify_manifest()
    if args.command == "verify":
        return
    with lock():
        if args.command == "download":
            run(ROOT / "src/download_sources.py", "--mode", "cached" if args.cached else "download", "--destination", str(ROOT / ".local/downloads"))
        elif args.command.startswith("nakdan-"):
            nakdan(args.command, args.retry_unfinished)
        elif args.command == "prepare":
            prepare()
        elif args.command == "analyze":
            analyze()
        elif args.command == "core":
            prepare()
            analyze()
            subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)
        elif args.command == "extend":
            extend()
        elif args.command == "compare":
            compare_modes()
        elif args.command == "figures":
            run(ROOT / "src" / "analysis" / "comparison_figures.py")


if __name__ == "__main__":
    main()
