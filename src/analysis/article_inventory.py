"""Regenerate Appendix A directly from rebuilt streams and comparison outputs."""
import csv, json
from pathlib import Path

P = Path(__file__).resolve().parents[2]
C = P / "results" / "comparison"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


coverage = [r for r in rows(C / "coverage.csv") if r["mode"] == "exact" and r["block"] == "512" and r["offset"] == "0" and r["radius"] == "64"]
spatial = [r for r in rows(C / "spatial.csv") if r["mode"] == "exact" and r["radius"] == "64" and r["control"] == "local128"]
spatial_by = {r["corpus"]: r for r in spatial}

core = json.loads((P / "results" / "corpus" / "segments.json").read_text(encoding="utf-8"))
units = {}
for segment in core:
    units[segment["corpus"]] = units.get(segment["corpus"], 0) + len(segment["sounds"])

additional_path = P / ".local" / "additional" / "segments_words.json"
if not additional_path.exists():
    raise FileNotFoundError("Additional sound streams are required; run `python project.py extend` first")
additional = json.loads(additional_path.read_text(encoding="utf-8"))
for corpus, segments in additional.items():
    units[corpus] = sum(len(unit) for segment in segments for word in segment for unit in word)

out = []
for row in coverage:
    corpus = row["corpus"]
    if corpus not in units:
        raise ValueError(f"No rebuilt sound-unit count for {corpus}")
    sp = spatial_by[corpus]
    out.append({
        "corpus": corpus,
        "sound_units": units[corpus],
        "spatial_blocks": int(sp["blocks"]),
        "spatial_retained_fraction": float(sp["retained_fraction"]),
        "coverage_blocks": int(row["blocks"]),
        "coverage_retained_fraction": float(row["retained_fraction"]),
    })

path = P / "results" / "article_corpus_inventory.csv"
with path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(out[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(out)
print(f"PASS article inventory: {len(out)} corpora, derived from rebuilt streams")
