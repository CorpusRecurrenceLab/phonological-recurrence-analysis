"""Validate paired exact/expanded outputs without creating an extra public report."""
import csv, json
from pathlib import Path

P = Path(__file__).resolve().parents[2]
A = P / "results" / "comparison"
V = P / ".local" / "validation"
V.mkdir(parents=True, exist_ok=True)


def read(name):
    with (A / f"{name}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


checks = 0
specs = [
    ("coverage", ["corpus", "block", "offset", "radius"], ["mean"]),
    ("distance", ["corpus", "cap", "block", "offset", "phase", "gap"], ["mean"]),
    ("spatial", ["corpus", "radius", "control"], ["observed", "null_mean"]),
    ("spatial_replicates", ["corpus", "radius", "control", "replicate"], ["coverage"]),
]
for name, keys, fields in specs:
    rows = read(name)
    exact = {tuple(row[k] for k in keys): row for row in rows if row["mode"] == "exact"}
    for row in rows:
        if row["mode"] != "expanded":
            continue
        base = exact[tuple(row[k] for k in keys)]
        for field in fields:
            if float(row[field]) + 1e-12 < float(base[field]):
                raise ValueError(f"Expanded value below exact in {name}: {row}")
            checks += 1
        for field in ("blocks", "retained_fraction", "anchors"):
            if field in row and row[field] != base[field]:
                raise ValueError(f"Paired material differs in {name}: {field}")

record = {"status": "PASS", "expanded_superset_checks": checks, "corpora": len({r['corpus'] for r in read('coverage')})}
(V / "comparison.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"PASS paired comparison: {checks} expanded-superset checks")
