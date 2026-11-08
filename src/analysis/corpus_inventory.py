"""Reproduce Appendix A in an untracked workspace and validate against frozen release.

Never overwrite a manifest-pinned output during a reproducibility run. Any
meaningful discrepancy creates a human-readable diagnostic in .local/validation.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

P = Path(__file__).resolve().parents[2]
C = P / "results" / "comparison"
FROZEN = P / "results" / "corpus_inventory.csv"
GENERATED = P / ".local" / "validation" / "corpus_inventory_generated.csv"
DIAGNOSTIC = P / ".local" / "validation" / "corpus_inventory_diff.json"
FIELDS = (
    "corpus", "sound_units", "spatial_blocks", "spatial_retained_fraction",
    "coverage_blocks", "coverage_retained_fraction",
)
INTEGER_FIELDS = {"sound_units", "spatial_blocks", "coverage_blocks"}
FLOAT_FIELDS = {"spatial_retained_fraction", "coverage_retained_fraction"}


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def compute_rows():
    coverage = [r for r in rows(C / "coverage.csv")
                if r["mode"] == "exact" and r["block"] == "512"
                and r["offset"] == "0" and r["radius"] == "64"]
    spatial = [r for r in rows(C / "spatial.csv")
               if r["mode"] == "exact" and r["radius"] == "64"
               and r["control"] == "local128"]
    spatial_by = {r["corpus"]: r for r in spatial}
    if len(spatial_by) != len(spatial):
        raise ValueError("Duplicate spatial corpus entries")

    core = json.loads((P / "results" / "corpus" / "segments.json").read_text(encoding="utf-8"))
    units = {}
    for segment in core:
        units[segment["corpus"]] = units.get(segment["corpus"], 0) + len(segment["sounds"])

    additional_path = P / ".local" / "additional" / "segments_words.json"
    if not additional_path.exists():
        raise FileNotFoundError("Additional streams required: run `python project.py extend` first")
    additional = json.loads(additional_path.read_text(encoding="utf-8"))
    for corpus, segments in additional.items():
        if corpus in units:
            raise ValueError(f"Additional corpus collides with base corpus: {corpus}")
        # Each word is a list of phonological units. A unit such as "sh" or
        # "ts" is ONE unit, not two ASCII characters.
        units[corpus] = sum(len(word) for segment in segments for word in segment)

    output = []
    for row in coverage:
        corpus = row["corpus"]
        if corpus not in units or corpus not in spatial_by:
            raise ValueError(f"Missing corpus data: {corpus}")
        sp = spatial_by[corpus]
        output.append({
            "corpus": corpus,
            "sound_units": units[corpus],
            "spatial_blocks": int(sp["blocks"]),
            "spatial_retained_fraction": float(sp["retained_fraction"]),
            "coverage_blocks": int(row["blocks"]),
            "coverage_retained_fraction": float(row["retained_fraction"]),
        })
    if len({r["corpus"] for r in output}) != len(output):
        raise ValueError("Duplicate corpus in study inventory")
    return output


def compare_inventory(actual, reference):
    """Exact counts and identities; 1e-12 tolerance for serialization of floats."""
    diffs = []
    if len(actual) != len(reference):
        diffs.append({"issue": "row_count", "actual": len(actual), "expected": len(reference)})
    for i, (a, b) in enumerate(zip(actual, reference)):
        for field in FIELDS:
            av, bv = a.get(field), b.get(field)
            if field in INTEGER_FIELDS:
                good = int(av) == int(bv)
            elif field in FLOAT_FIELDS:
                good = math.isclose(float(av), float(bv), rel_tol=1e-12, abs_tol=1e-12)
            else:
                good = av == bv
            if not good:
                diffs.append({"row": i + 1, "corpus": a.get("corpus"), "field": field,
                              "actual": av, "expected": bv})
    return diffs


def main():
    generated = compute_rows()
    GENERATED.parent.mkdir(parents=True, exist_ok=True)
    with GENERATED.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(generated)
    reference = rows(FROZEN)
    discrepancies = compare_inventory(generated, reference)
    if discrepancies:
        DIAGNOSTIC.write_text(json.dumps({"status": "FAIL", "discrepancies": discrepancies},
                                         indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        raise ValueError(f"study inventory differs from frozen release: {len(discrepancies)} fields; "
                         f"see {DIAGNOSTIC.relative_to(P)}")
    DIAGNOSTIC.unlink(missing_ok=True)
    print(f"PASS study inventory: {len(generated)} corpora match frozen release; "
          "generated copy is in .local/validation")


if __name__ == "__main__":
    main()
