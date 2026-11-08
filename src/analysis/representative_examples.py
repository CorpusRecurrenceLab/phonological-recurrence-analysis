"""Generate mechanically selected examples used by Supplementary Material S1."""
from __future__ import annotations
import bisect, csv, json, sys
from collections import defaultdict
from pathlib import Path

P = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(P / "src" / "analysis"))
from spatial import corpus_words
from compare_modes import occurrences

DISTRIBUTED = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges",
    "modern_523", "modern_7924", "modern_884",
]
NONREDISTRIBUTED = ["rivlin_ali_baba", "bialik_beir_haharegah"]
DISPLAY = {
    "Genesis": "Genesis", "Exodus": "Exodus", "Leviticus": "Leviticus", "Numbers": "Numbers",
    "Deuteronomy": "Deuteronomy", "Joshua": "Joshua", "Judges": "Judges",
    "modern_523": "Brenner — Mikan u-mikan",
    "modern_7924": "Ahad Ha-Am — Shilton ha-sekhel",
    "modern_884": "Tchernichovsky — Hatunata shel Elka",
    "rivlin_ali_baba": "Rivlin — Ali Baba",
    "bialik_beir_haharegah": "Bialik — Be-ir ha-haregah",
}


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def top_exact_motifs(sound_units, radius=64):
    by = defaultdict(list)
    for motif, position in occurrences(sound_units):
        by[motif].append(position)
    counts = []
    for motif, positions in by.items():
        qualified = 0
        for i, pos in enumerate(positions):
            lo = bisect.bisect_left(positions, pos - radius)
            hi = bisect.bisect_right(positions, pos + radius)
            if any(abs(pos - other) >= 3 for other in positions[lo:hi]):
                qualified += 1
        if qualified:
            counts.append((qualified, "".join(motif)))
    counts.sort(key=lambda x: (-x[0], x[1]))
    return [{"motif": motif, "qualifying_occurrences": count} for count, motif in counts[:5]]


def selected_words(word_segments, segment_index, corpus_start, length=512):
    segment_offsets = []
    pos = 0
    word_base = 0
    for idx, segment in enumerate(word_segments):
        segment_units = sum(len(word) for word in segment)
        segment_offsets.append((pos, pos + segment_units, word_base))
        pos += segment_units
        word_base += len(segment)
    seg_a, seg_b, word_base = segment_offsets[segment_index]
    local_start = corpus_start - seg_a
    local_end = local_start + length
    words = []
    unit_pos = 0
    first_index = None
    last_index = None
    block_units = []
    for j, word in enumerate(word_segments[segment_index]):
        a, b = unit_pos, unit_pos + len(word)
        if b > local_start and a < local_end:
            if first_index is None:
                first_index = word_base + j
            last_index = word_base + j
            words.append("".join(word))
        # exact 512-unit block, independent of word boundaries
        overlap_a = max(a, local_start)
        overlap_b = min(b, local_end)
        if overlap_a < overlap_b:
            block_units.extend(word[overlap_a - a:overlap_b - a])
        unit_pos = b
    if len(block_units) != length:
        raise ValueError(f"Selected block length mismatch: {len(block_units)} != {length}")
    return words, first_index, last_index, block_units


def biblical_span(corpus, start, end, readings):
    pos = 0
    refs = []
    for row in readings:
        if not row["ref"].startswith(corpus + " "):
            continue
        a, b = pos, pos + len(row["sounds"])
        if b > start and a < end:
            refs.append(row["ref"])
        pos = b
    if not refs:
        return None
    return refs[0] if len(refs) == 1 else f"{refs[0]}–{refs[-1]}"


def main():
    density = read_csv(P / "results" / "comparison" / "density.csv")
    words = corpus_words(additional=False)
    readings = json.loads((P / "results" / "corpus" / "readings.json").read_text(encoding="utf-8"))
    output = []

    for corpus in DISTRIBUTED:
        exact_rows = [r for r in density if r["corpus"] == corpus and r["mode"] == "exact"]
        if not exact_rows:
            raise ValueError(f"No exact density rows for {corpus}")
        maximum = max(float(r["coverage"]) for r in exact_rows)
        selected = min((r for r in exact_rows if abs(float(r["coverage"]) - maximum) < 1e-15), key=lambda r: int(r["start"]))
        start = int(selected["start"]); segment = int(selected["segment"]); length = int(selected["length"])
        expanded = next(r for r in density if r["corpus"] == corpus and r["mode"] == "expanded" and r["segment"] == selected["segment"] and r["start"] == selected["start"] and r["length"] == selected["length"])
        detector_words, first_word, last_word, block_units = selected_words(words[corpus], segment, start, length)
        span = biblical_span(corpus, start, start + length, readings) if corpus in {"Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges"} else None
        output.append({
            "corpus": corpus,
            "display_name": DISPLAY[corpus],
            "selection": "first complete 512-unit block attaining the corpus maximum exact R64 coverage",
            "segment": segment,
            "sound_start": start,
            "sound_length": length,
            "verse_span": span,
            "word_index_start_zero_based": first_word if span is None else None,
            "word_index_end_zero_based": last_word if span is None else None,
            "exact_coverage": float(selected["coverage"]),
            "expanded_coverage": float(expanded["coverage"]),
            "detector_encoding_excerpt": " ".join(detector_words),
            "top_exact_triplets": top_exact_motifs(block_units, 64),
        })

    for corpus in NONREDISTRIBUTED:
        exact_rows = [r for r in density if r["corpus"] == corpus and r["mode"] == "exact"]
        selected = min(exact_rows, key=lambda r: int(r["start"]))
        expanded = next(r for r in density if r["corpus"] == corpus and r["mode"] == "expanded" and r["segment"] == selected["segment"] and r["start"] == selected["start"] and r["length"] == selected["length"])
        output.append({
            "corpus": corpus,
            "display_name": DISPLAY[corpus],
            "selection": "fixed opening complete 512-unit block; not score-selected",
            "segment": int(selected["segment"]),
            "sound_start": int(selected["start"]),
            "sound_length": int(selected["length"]),
            "verse_span": None,
            "word_index_start_zero_based": None,
            "word_index_end_zero_based": None,
            "exact_coverage": float(selected["coverage"]),
            "expanded_coverage": float(expanded["coverage"]),
            "detector_encoding_excerpt": None,
            "top_exact_triplets": None,
            "note": "Complete source text is not redistributed; no source-derived excerpt is serialized in this public result file."
        })

    path = P / "results" / "representative_examples.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"PASS representative examples: {len(output)} fixed cases")


if __name__ == "__main__":
    main()
