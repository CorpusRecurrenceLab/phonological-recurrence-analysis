#!/usr/bin/env python3
"""Prepare the frozen Tanakh-wide source and reading layer.

This script intentionally performs *preparation only*.  It does not compute the
study's Tanakh-wide statistics.  It downloads the 39 frozen source JSON files
from the exact pinned Git commit, verifies their Git blob ids,
constructs the Masoretic reading stream, applies the frozen source exceptions, runs the frozen computational transcription, and verifies every
book-level count against config/preparation_expected.json.

Python: standard library only (tested target: Python 3.12 on Windows).
"""
from __future__ import annotations

import argparse
import shutil
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src" / "core"
sys.path.insert(0, str(ROOT / "src" / "preparation"))
sys.path.insert(0, str(CORE))

from perpetual_qere import normalize as normalize_perpetual_qere  # noqa: E402
from phonetic_core_v2 import transliterate_word  # noqa: E402
from prepare_biblical_reading import adapt  # noqa: E402

TOKEN = re.compile(r"[א-ת][א-ת\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]*")
MAQAF = "\u05BE"
HEBREW_LETTERS = set("אבגדהוזחטיכלמנסעפצקרשתךםןףץ")
FINAL_TO_BASE = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def normalized_letters(text: str) -> str:
    return "".join(FINAL_TO_BASE.get(ch, ch) for ch in text if ch in HEBREW_LETTERS)


def fnv1a64_utf8(text: str) -> str:
    h = 0xCBF29CE484222325
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{h:016x}"


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def block_count(n: int, length: int, offset: int) -> int:
    return (n - offset) // length if n >= offset + length else 0


def safe_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def strip_editorial_tail(source: str, ref: str, rules: dict[str, dict]):
    rule = rules.get(ref)
    if rule is None:
        if "<" in source or ">" in source:
            raise ValueError(f"Unexpected HTML/editorial markup at {ref}")
        return source, None
    suffix = rule["suffix"]
    if not source.endswith(suffix):
        raise ValueError(f"Frozen editorial-tail suffix mismatch at {ref}")
    base = source[: -len(suffix)]
    if "<" in base or ">" in base:
        raise ValueError(f"Unexpected additional HTML/editorial markup at {ref}")
    return base, {
        "kind": "editorial_repeat_tail",
        "original": suffix,
        "replacement": "",
        "meaning": rule["meaning"],
    }


def omit_ketiv_without_qere(reading: str, ref: str, rules: dict[str, dict]):
    rule = rules.get(ref)
    if rule is None:
        return reading, None
    matches = list(TOKEN.finditer(reading))
    idx = int(rule["token_index_before_omission"])
    if not (1 <= idx <= len(matches)):
        raise ValueError(f"ketiv-without-qere token index out of range at {ref}")
    match = matches[idx - 1]
    expected = normalized_letters(rule["surface"])
    observed = normalized_letters(match.group())
    if observed != expected:
        raise ValueError(
            f"ketiv-without-qere surface mismatch at {ref}: "
            f"expected {rule['surface']!r}, observed {match.group()!r}"
        )
    start, end = match.span()
    # Remove one adjacent maqaf so the remaining reading stream has no dangling joiner.
    if end < len(reading) and reading[end] == MAQAF:
        end += 1
    elif start > 0 and reading[start - 1] == MAQAF:
        start -= 1
    original = reading[start:end]
    return reading[:start] + reading[end:], {
        "kind": "ketiv_without_qere",
        "token_index_before_omission": idx,
        "surface": match.group(),
        "original": original,
        "replacement": "",
        "note": rule["note"],
    }


def is_aramaic_token(book: str, chapter: int, verse: int, token_index: int) -> bool:
    # Frozen masks are deliberately explicit rather than language-detected.
    if book == "Genesis":
        return chapter == 31 and verse == 47 and token_index in (4, 5)
    if book == "Jeremiah":
        return chapter == 10 and verse == 11
    if book == "Daniel":
        return (
            (chapter == 2 and verse == 4 and token_index >= 5)
            or (chapter == 2 and verse >= 5)
            or (3 <= chapter <= 6)
            or (chapter == 7 and verse <= 28)
        )
    if book == "Ezra":
        return (
            (chapter == 4 and verse >= 8)
            or chapter == 5
            or (chapter == 6 and verse <= 18)
            or (chapter == 7 and 12 <= verse <= 26)
        )
    return False


def download_frozen_source(book_row: dict, mirror_commit: str, raw_dir: Path, offline: bool) -> bytes:
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = raw_dir / f"{int(book_row['order']):02d}_{safe_slug(book_row['source_book'])}.json"
    if target.exists():
        data = target.read_bytes()
    else:
        # The distributed 39-book release contains pinned source bytes. Reuse
        # them before contacting the mirror, including in a clean offline clone.
        bundled = ROOT / "sources" / "original" / "tanakh" / target.name
        if bundled.is_file():
            data = bundled.read_bytes()
        elif offline:
            raise FileNotFoundError(
                f"Missing frozen source in offline mode: {target} or {bundled}"
            )
        else:
            quoted = urllib.parse.quote(book_row["mirror_path"], safe="/")
            url = (
                "https://raw.githubusercontent.com/"
                "Sivan22/Sefaria-Export-Hebrew-Texts/"
                f"{mirror_commit}/{quoted}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "tanakh-stage2-freeze/1"})
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()
        # A file is cached only after the hash check below succeeds.
    got = git_blob_sha1(data)
    if got != book_row["git_blob_sha1"]:
        raise ValueError(
            f"Git blob mismatch for {book_row['source_book']}: "
            f"expected {book_row['git_blob_sha1']}, got {got}"
        )
    if not target.exists():
        target.write_bytes(data)
    return data


def assert_source_metadata(obj: dict, freeze: dict, book: str):
    src = freeze["source"]
    checks = {
        "versionTitle": src["version_title"],
        "versionSource": src["version_source"],
        "language": src["language_metadata"],
        "license": src["license"],
    }
    for key, expected in checks.items():
        observed = obj.get(key)
        if observed != expected:
            raise ValueError(
                f"Source metadata mismatch for {book} / {key}: "
                f"expected {expected!r}, got {observed!r}"
            )


def compare_frozen_row(observed: dict, expected: dict):
    keys = [
        "order", "canonical_section", "source_book", "traditional_24_book",
        "mirror_path", "git_blob_sha1", "chapter_count", "verse_count",
        "prepared_fnv1a64", "word_count", "sound_unit_count",
        "explicit_qere_edits", "section_markers_removed", "inverted_nun_removed",
        "ketiv_without_qere_omissions", "editorial_repeat_tails_removed",
        "perpetual_qere", "aramaic_word_count", "aramaic_sound_unit_count",
        "hebrew_only_word_count", "hebrew_only_sound_unit_count",
        "unresolved_tokens", "geometry_complete_blocks",
    ]
    bad = []
    for key in keys:
        if observed.get(key) != expected.get(key):
            bad.append((key, expected.get(key), observed.get(key)))
    if bad:
        msg = "; ".join(f"{k}: expected={e!r} observed={o!r}" for k, e, o in bad)
        raise AssertionError(f"Frozen preparation regression mismatch for {expected['source_book']}: {msg}")


def process_book(book_row: dict, expected: dict, configs: dict, freeze: dict, work: Path, offline: bool, publish: bool = False):
    data = download_frozen_source(book_row, freeze["source"]["mirror_commit"], work / "sources_raw", offline)
    obj = json.loads(data.decode("utf-8"))
    book = book_row["source_book"]
    assert_source_metadata(obj, freeze, book)
    text = obj.get("text")
    if not isinstance(text, list) or not all(isinstance(ch, list) for ch in text):
        raise ValueError(f"Unexpected text shape for {book}")
    if len(text) != int(book_row["chapter_count"]):
        raise ValueError(f"Chapter-count mismatch for {book}")
    if sum(len(ch) for ch in text) != int(book_row["verse_count"]):
        raise ValueError(f"Verse-count mismatch for {book}")

    prepared_verses: list[str] = []
    audit_rows: list[dict] = []
    word_count = sound_count = 0
    aramaic_words = aramaic_sounds = 0
    qere_edits = section_edits = nun_edits = 0
    kwq_omissions = apparatus_removed = 0
    pq_counts = {"qere_hi": 0, "qere_yerushalayim": 0, "qere_yissakhar": 0}
    unresolved: list[str] = []

    for c_idx, chapter in enumerate(text, 1):
        for v_idx, source in enumerate(chapter, 1):
            ref = f"{book} {c_idx}:{v_idx}"
            source_for_reading, apparatus_edit = strip_editorial_tail(
                source, ref, configs["editorial"]
            )
            if apparatus_edit:
                apparatus_removed += 1
            reading, edits, _spans = adapt(source_for_reading)
            for edit in edits:
                if edit["kind"] == "qere":
                    qere_edits += 1
                elif edit["kind"] == "section":
                    section_edits += 1
                elif edit["kind"] == "inverted_nun":
                    nun_edits += 1
                else:
                    raise ValueError(f"Unexpected adapter edit kind at {ref}: {edit['kind']}")

            reading, kwq_edit = omit_ketiv_without_qere(reading, ref, configs["kwq"])
            if kwq_edit:
                kwq_omissions += 1

            if re.search(r"[\[\]()<>]", reading):
                raise ValueError(f"Unrecognized source annotation survives at {ref}")

            token_index = 0
            verse_word_count = verse_sound_count = 0
            for match in TOKEN.finditer(reading):
                token_index += 1
                word_count += 1
                verse_word_count += 1
                token = match.group()
                _normalized, pq_rules = normalize_perpetual_qere(token)
                for rule in pq_rules:
                    if rule not in pq_counts:
                        raise ValueError(f"Unexpected perpetual-qere rule at {ref}: {rule}")
                    pq_counts[rule] += 1
                units = transliterate_word(token, return_units=True)
                if not units:
                    unresolved.append(f"{ref}#{token_index}:{token}")
                    continue
                sound_count += len(units)
                verse_sound_count += len(units)
                if is_aramaic_token(book, c_idx, v_idx, token_index):
                    aramaic_words += 1
                    aramaic_sounds += len(units)

            prepared_verses.append(reading)
            if apparatus_edit or edits or kwq_edit:
                audit_rows.append({
                    "ref": ref,
                    "source": source,
                    "reading": reading,
                    "editorial_repeat_tail": apparatus_edit,
                    "adapter_edits": edits,
                    "ketiv_without_qere": kwq_edit,
                    "word_count": verse_word_count,
                    "sound_unit_count": verse_sound_count,
                })

    prepared_text = "\n".join(prepared_verses) + "\n"
    out_dir = work / "sources_prepared" / safe_slug(book)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "text.txt").write_text(prepared_text, encoding="utf-8", newline="\n")
    with (out_dir / "changes.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for row in audit_rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    observed = {
        "order": int(book_row["order"]),
        "canonical_section": book_row["canonical_section"],
        "source_book": book,
        "traditional_24_book": book_row["traditional_24_book"],
        "mirror_path": book_row["mirror_path"],
        "git_blob_sha1": book_row["git_blob_sha1"],
        "chapter_count": len(text),
        "verse_count": sum(len(ch) for ch in text),
        "prepared_fnv1a64": fnv1a64_utf8(prepared_text),
        "word_count": word_count,
        "sound_unit_count": sound_count,
        "explicit_qere_edits": qere_edits,
        "section_markers_removed": section_edits,
        "inverted_nun_removed": nun_edits,
        "ketiv_without_qere_omissions": kwq_omissions,
        "editorial_repeat_tails_removed": apparatus_removed,
        "perpetual_qere": pq_counts,
        "aramaic_word_count": aramaic_words,
        "aramaic_sound_unit_count": aramaic_sounds,
        "hebrew_only_word_count": word_count - aramaic_words,
        "hebrew_only_sound_unit_count": sound_count - aramaic_sounds,
        "unresolved_tokens": unresolved,
        "geometry_complete_blocks": {
            "block_512_offset_0": block_count(sound_count, 512, 0),
            "block_512_offset_256": block_count(sound_count, 512, 256),
            "block_1280_offset_0": block_count(sound_count, 1280, 0),
            "block_1280_offset_640": block_count(sound_count, 1280, 640),
            "block_4352_offset_0": block_count(sound_count, 4352, 0),
            "block_4352_offset_2176": block_count(sound_count, 4352, 2176),
            # Upper bound only: final spatial geometry respects segment boundaries later.
            "spatial_128word_upper_bound": word_count // 128,
        },
    }
    compare_frozen_row(observed, expected)
    # Publish only after all validations for this book succeeded. The canonical
    # downloaded bytes are NOT interchangeable with separately pinned comparison *_verses.json source variants.
    if publish:
        canonical = ROOT / "sources" / "original" / "tanakh"
        canonical.mkdir(parents=True, exist_ok=True)
        source_name = f"{int(book_row['order']):02d}_{safe_slug(book)}.json"
        raw_bytes = data
        dest = canonical / source_name
        if not dest.exists() or dest.read_bytes() != raw_bytes:
            dest.write_bytes(raw_bytes)
        prepared_dest = ROOT / "sources" / "prepared" / "tanakh" / safe_slug(book)
        prepared_dest.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out_dir / "text.txt", prepared_dest / "text.txt")
        shutil.copyfile(out_dir / "changes.jsonl", prepared_dest / "changes.jsonl")
    return observed


def aggregate(rows: list[dict], traditional_count: int) -> tuple[dict, dict]:
    totals = {
        "source_books": len(rows),
        "traditional_books": traditional_count,
        "chapters": sum(r["chapter_count"] for r in rows),
        "verses": sum(r["verse_count"] for r in rows),
        "words": sum(r["word_count"] for r in rows),
        "sound_units": sum(r["sound_unit_count"] for r in rows),
        "explicit_qere_edits": sum(r["explicit_qere_edits"] for r in rows),
        "section_markers_removed": sum(r["section_markers_removed"] for r in rows),
        "inverted_nun_removed": sum(r["inverted_nun_removed"] for r in rows),
        "ketiv_without_qere_omissions": sum(r["ketiv_without_qere_omissions"] for r in rows),
        "editorial_repeat_tails_removed": sum(r["editorial_repeat_tails_removed"] for r in rows),
        "unresolved_tokens": sum(len(r["unresolved_tokens"]) for r in rows),
        "aramaic_words": sum(r["aramaic_word_count"] for r in rows),
        "aramaic_sound_units": sum(r["aramaic_sound_unit_count"] for r in rows),
        "hebrew_only_words": sum(r["hebrew_only_word_count"] for r in rows),
        "hebrew_only_sound_units": sum(r["hebrew_only_sound_unit_count"] for r in rows),
    }
    pq = {
        key: sum(r["perpetual_qere"][key] for r in rows)
        for key in ("qere_hi", "qere_yerushalayim", "qere_yissakhar")
    }
    return totals, pq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--work-dir",
        default=str(ROOT / ".local" / "tanakh" / "preparation"),
        help="cache/output directory (default: package/work)",
    )
    ap.add_argument(
        "--offline",
        action="store_true",
        help="do not download; use verified bundled sources or cached files",
    )
    ap.add_argument("--publish-sources", action="store_true", help="publish validated 39-book raw and prepared sources to sources/ trees")
    args = ap.parse_args()
    work = Path(args.work_dir).resolve()
    work.mkdir(parents=True, exist_ok=True)

    freeze = load_json("config/tanakh/source_freeze.json")
    expected = load_json("config/tanakh/preparation_expected.json")
    map24 = load_json("config/tanakh/traditional_24_map.json")
    kwq_cfg = load_json("config/tanakh/ketiv_without_qere.json")
    editorial_cfg = load_json("config/tanakh/editorial_repeat_tails.json")
    _aramaic_cfg = load_json("config/tanakh/aramaic_masks.json")  # policy record; logic above is frozen explicitly
    configs = {
        "kwq": {r["ref"]: r for r in kwq_cfg["rules"]},
        "editorial": {r["ref"]: r for r in editorial_cfg["rules"]},
    }

    if freeze["source"]["mirror_commit"] != expected["source_mirror_commit"]:
        raise AssertionError("Source-freeze / preparation mirror-commit mismatch")
    if freeze["base_release"]["github_base_commit"] != expected["base_project_commit"]:
        raise AssertionError("Source-freeze / preparation base-code commit mismatch")

    frozen_rows = freeze["source_books"]
    exp_by_book = {r["source_book"]: r for r in expected["source_books"]}
    if len(frozen_rows) != 39 or len(exp_by_book) != 39:
        raise AssertionError("Expected exactly 39 frozen source books")

    results = []
    for row in frozen_rows:
        book = row["source_book"]
        print(f"[{int(row['order']):02d}/39] {book} ...", flush=True)
        results.append(process_book(row, exp_by_book[book], configs, freeze, work, args.offline, args.publish_sources))

    traditional_count = len(map24["traditional_books"])
    totals, pq = aggregate(results, traditional_count)
    if totals != expected["counts"]:
        raise AssertionError(f"Aggregate preparation counts mismatch:\nexpected={expected['counts']}\nobserved={totals}")
    if pq != expected["perpetual_qere_totals"]:
        raise AssertionError(f"Aggregate perpetual-qere counts mismatch: expected={expected['perpetual_qere_totals']} observed={pq}")

    generated = {
        "schema": expected["schema"],
        "base_project_commit": expected["base_project_commit"],
        "source_mirror_commit": expected["source_mirror_commit"],
        "counts": totals,
        "perpetual_qere_totals": pq,
        "source_books": results,
        "status": "PASS",
    }
    (work / "generated_preparation_inventory.json").write_text(
        json.dumps(generated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("PASS Preparation preparation: 39/39 source books")
    print(f"PASS words / sound units: {totals['words']:,} / {totals['sound_units']:,}")
    print(f"PASS Aramaic-exclusion retained inventory: {totals['hebrew_only_words']:,} / {totals['hebrew_only_sound_units']:,}")
    print("PASS unresolved tokens: 0")
    print("No recurrence statistic is computed by this preparation script.")


if __name__ == "__main__":
    main()
