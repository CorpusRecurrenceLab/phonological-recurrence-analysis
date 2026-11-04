"""Final structural checks for the public reproducibility release."""
from __future__ import annotations
import csv, hashlib, json, re
from pathlib import Path

P = Path(__file__).resolve().parents[2]
V = P / ".local" / "validation"
V.mkdir(parents=True, exist_ok=True)


def csv_rows(rel):
    with (P / rel).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


checks = []

def ok(name, condition):
    if not condition:
        raise ValueError(f"Release validation failed: {name}")
    checks.append(name)

coverage = csv_rows("results/comparison/coverage.csv")
distance = csv_rows("results/comparison/distance.csv")
spatial = csv_rows("results/comparison/spatial.csv")
density = csv_rows("results/comparison/density.csv")
corpora = sorted({r["corpus"] for r in coverage})
ok("twelve comparison corpora", len(corpora) == 12)
ok("paired coverage modes", {r["mode"] for r in coverage} == {"exact", "expanded"})
ok("coverage grid nonempty", len(coverage) == 288)
ok("distance grid nonempty", len(distance) > 1000)
ok("spatial grid complete", len(spatial) == 216)
ok("density contains all corpora", {r["corpus"] for r in density} == set(corpora))

inventory = csv_rows("results/article_corpus_inventory.csv")
ok("inventory has twelve corpora", len(inventory) == 12 and {r["corpus"] for r in inventory} == set(corpora))

qamats = csv_rows("results/qamats_kol_sensitivity.csv")
ok("qamats diagnostic ten rows", len(qamats) == 10)
ok("qamats maximum under 0.1 pp", max(abs(float(r["difference_percentage_points"])) for r in qamats) < 0.1)

examples = json.loads((P / "results" / "representative_examples.json").read_text(encoding="utf-8"))
ok("twelve representative cases", len(examples) == 12 and {r["corpus"] for r in examples} == set(corpora))
ok("Ahad Ha-Am representative case present", any(r["corpus"] == "modern_7924" for r in examples))

selection = json.loads((P / "examples" / "close_reading_selection.json").read_text(encoding="utf-8"))
ok("46 close-reading references", selection["weak_case_set"]["count"] + selection["score_independent_sample"]["count"] == 46)

expected_outputs = json.loads((P / "config" / "published_outputs.json").read_text(encoding="utf-8"))
for rel, digest in expected_outputs.items():
    path = P / rel
    ok(f"published output present: {rel}", path.is_file())
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    ok(f"published output hash: {rel}", actual == digest)

for rel in ["README.md", "REPRODUCE_ARTICLE.md", "protocols/sources.md", "protocols/transcription.md", "protocols/analysis.md", "protocols/spatial_control.md", "protocols/exact_expanded_comparison.md"]:
    text = (P / rel).read_text(encoding="utf-8")
    ok(f"no Cyrillic working prose in {rel}", not re.search(r"[А-Яа-яЁё]", text))

record = {"status": "PASS", "checks": checks, "count": len(checks)}
(V / "release.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"PASS release validation: {len(checks)} checks")
