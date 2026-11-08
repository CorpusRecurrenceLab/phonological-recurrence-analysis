"""Build exact-mode regression intermediates for the two non-redistributed additions."""
import json, sys
from pathlib import Path
from spatial import P, corpus_words
from finish import coverage_table


def main():
    if "--additional" not in sys.argv:
        raise ValueError("supplement.py requires --additional")
    words = corpus_words(additional=True)
    extra = {k: v for k, v in words.items() if k in {"rivlin_ali_baba", "bialik_beir_haharegah"}}
    raw = [
        {"corpus": corpus, "segment": i, "sounds": [u for word in segment for u in word]}
        for corpus, segments in extra.items()
        for i, segment in enumerate(segments)
    ]
    if set(extra) != {"rivlin_ali_baba", "bialik_beir_haharegah"}:
        raise ValueError("Both additional corpora are required")
    out = P / "results" / "analysis" / "additional"
    out.mkdir(parents=True, exist_ok=True)
    rows = coverage_table(raw, 512) + coverage_table(raw, 1280)
    (out / "coverage.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8", newline="\n")
    import run_matched
    run_matched.main(raw, out)
    print("PASS additional exact-mode intermediates")


if __name__ == "__main__":
    main()
