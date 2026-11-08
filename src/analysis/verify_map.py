"""Rebuild the Pentateuchal verse map and compare it with the frozen reference."""
import bisect, csv, json
from collections import defaultdict
from pathlib import Path

P = Path(__file__).resolve().parents[2]
V = set("aeiou")
PAIRS = [("f","v"),("p","b"),("d","t"),("b","v"),("z","s"),("h","kh"),("q","k")]
ADJ = defaultdict(set)
for a, b in PAIRS:
    ADJ[a].add(b); ADJ[b].add(a)


def main():
    readings = json.loads((P / "results" / "corpus" / "readings.json").read_text(encoding="utf-8"))
    books = defaultdict(list)
    for row in readings:
        book = row["ref"].split()[0]
        if book in {"Genesis","Exodus","Leviticus","Numbers","Deuteronomy"}:
            books[book].append(row)
    rows = []
    for book, verses in books.items():
        seq = []; bounds = []
        for row in verses:
            a = len(seq); seq.extend(row["sounds"]); bounds.append((a, len(seq), row["ref"]))
        occ = defaultdict(list); valid = {}
        for i in range(len(seq)-2):
            motif = tuple(seq[i:i+3]); nv = sum(x in V for x in motif)
            if 0 < nv < 3:
                occ[motif].append(i); valid[i] = motif

        def candidates(motif, expanded):
            yield motif
            if expanded:
                for k, item in enumerate(motif):
                    for replacement in ADJ.get(item, ()):
                        trial = list(motif); trial[k] = replacement; yield tuple(trial)

        def has_partner(i, motif, radius, expanded, lo_bound=0, hi_bound=None):
            hi_bound = len(seq) if hi_bound is None else hi_bound
            for candidate in candidates(motif, expanded):
                positions = occ.get(candidate, ())
                lo = bisect.bisect_left(positions, max(lo_bound, i-radius))
                hi = bisect.bisect_right(positions, min(hi_bound-3, i+radius))
                if any(abs(i-j) >= 3 for j in positions[lo:hi]):
                    return True
            return False

        for radius in (32,64,128):
            for a, b, ref in bounds:
                marks = {k:set() for k in ("exact","expanded","internal_exact","internal_expanded")}
                for i in range(max(0,a-2), min(b,len(seq)-2)):
                    motif = valid.get(i)
                    if motif is None: continue
                    if has_partner(i,motif,radius,False): marks["exact"].update(range(max(a,i),min(b,i+3)))
                    if has_partner(i,motif,radius,True): marks["expanded"].update(range(max(a,i),min(b,i+3)))
                for i in range(a,b-2):
                    motif = valid.get(i)
                    if motif is None: continue
                    if has_partner(i,motif,radius,False,a,b): marks["internal_exact"].update(range(i,i+3))
                    if has_partner(i,motif,radius,True,a,b): marks["internal_expanded"].update(range(i,i+3))
                units = b-a
                rows.append({"book":book,"ref":ref,"radius":radius,"units":units,**{k:len(v)/units for k,v in marks.items()}})

    frozen_map = json.loads((P / "reference" / "verse_map.json").read_text(encoding="utf-8"))
    if rows != frozen_map:
        raise ValueError("Rebuilt verse map differs from frozen reference")
    summary = []
    for radius in (32,64,128):
        current = [r for r in rows if r["radius"] == radius]
        for mode in ("exact","expanded","internal_exact","internal_expanded"):
            summary.append({
                "radius": radius,
                "mode": mode,
                "verses": len(current),
                "positive": sum(r[mode] > 0 for r in current),
                "coverage": sum(r[mode]*r["units"] for r in current) / sum(r["units"] for r in current),
                "zeros": [r["ref"] for r in current if r[mode] == 0],
            })
    frozen_summary = json.loads((P / "reference" / "verse_summary.json").read_text(encoding="utf-8"))
    if summary != frozen_summary:
        raise ValueError("Rebuilt verse summary differs from frozen reference")
    out = P / "results" / "analysis"; out.mkdir(parents=True, exist_ok=True)
    (out / "verse_map.json").write_text(json.dumps(rows), encoding="utf-8", newline="\n")
    (out / "verse_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    with (P / "results" / "verse_presence.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["radius","mode","verse_records","positive_records","weighted_coverage"], lineterminator='\n')
        writer.writeheader()
        for row in summary:
            writer.writerow({"radius":row["radius"],"mode":row["mode"],"verse_records":row["verses"],"positive_records":row["positive"],"weighted_coverage":row["coverage"]})
    print(f"PASS verse map: {len([r for r in rows if r['radius']==64])} frozen Pentateuchal verse records")


if __name__ == "__main__":
    main()
