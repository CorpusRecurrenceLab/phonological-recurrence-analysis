# Tanakh-wide Phonological Recurrence Analysis

This repository is the frozen reproducibility package for a Tanakh-wide analysis of order-sensitive phonological recurrence in the Masoretic reading stream.

The computational corpus comprises **39 Sefaria source-books**, reported also as the traditional **24 books of the Tanakh**. The primary analysis retains the complete declared reading stream, including Biblical Aramaic. A separate **Aramaic-span exclusion sensitivity** tests dependence on the declared Aramaic spans; a complementary Aramaic-only descriptive check applies the same unchanged geometry where sufficient material exists.

The repository is not a prose/poetry classifier. No book is removed or reclassified after results are inspected, and no radius, block size, distance gap, matching rule, fragment size, or permutation seed is tuned to the Tanakh-wide outcomes.

## Frozen provenance

- Source version: `Tanach with Ta'amei Hamikra` (Sefaria metadata source: tanach.us; Public Domain).
- Pinned source mirror: `Sivan22/Sefaria-Export-Hebrew-Texts`.
- Mirror commit: `0f41148df41c0fe47321a7da7c01390b7ad7e872`.
- Exact Git blob SHA-1 is frozen for every source JSON in `config/source_freeze.json`.
- The executable transcription core is byte-identical to the frozen base project files recorded in `config/base_code_freeze.json` (base commit `a58c44c650bea66f73398ae05c2542b74835566e`).

Source JSON files are not duplicated in this repository. `src/prepare.py` downloads each file from the pinned commit, verifies its Git blob id, and stops on any mismatch. Once cached, the preparation can be rerun offline.

## Requirements

Python 3.12 or newer. The project uses only the Python standard library.

## Reproduce

From the repository root on Windows:

```bat
run\RUN_ALL.bat
```

This performs, in order:

1. exact-source acquisition and reading-layer preparation;
2. the full primary 39-source-book / 24-book analysis;
3. the Aramaic-span exclusion and Aramaic-only checks;
4. release validation.

After the first successful run, cached source JSON files can be reused offline:

```bat
py -3.12 project.py all --offline
```

Static validation of the frozen repository itself requires no network access:

```bat
run\VERIFY.bat
```

Cross-platform equivalents:

```text
python project.py verify
python project.py prepare
python project.py primary
python project.py sensitivity
python project.py all
```

## Repository layout

- `src/core/` — frozen transcription and source-adapter core.
- `src/prepare.py` — source acquisition, reading adaptation, exact exception handling, and preparation regression checks.
- `src/primary.py` — complete frozen coverage, distance, and fragment-preserving spatial analysis.
- `src/aramaic_sensitivity.py` — hard-gap Aramaic-span exclusion and Aramaic-only descriptive checks.
- `config/` — pinned source manifest, explicit exception tables, language masks, and frozen expected values.
- `protocols/` — source, transcription, analysis, boundary, reporting, and sensitivity definitions.
- `results/primary/` — frozen primary source-book and traditional-book tables.
- `results/sensitivity/` — frozen Aramaic-span sensitivity tables.
- `run/` — Windows launchers.
- `tests/` — small deterministic smoke/regression tests.

Generated source caches and full-grid JSON outputs are written only under ignored `work/`.

## Primary readouts

The complete parameter grids are always computed before the primary summaries are extracted.

- **Coverage:** 512-unit block, offset 0, radius 64.
- **Distance:** cap 1024; adjacent minus gap-1024; equal mean of the four fixed offset/phase condition means.
- **Spatial:** radius-64 observed minus mean permutation coverage, separately for `local128`, `regional1024`, and `whole_corpus`.
- **Modes:** exact and restricted expanded correspondence.

Impossible fixed geometries are reported as `NA`; parameters are never reduced to rescue a short book.

## Important boundary rules

The 39 Sefaria source-books are the computational units. Samuel, Kings, the Twelve, Ezra-Nehemiah, and Chronicles are combined only for traditional 24-book reporting; no motif/window/block/fragment is manufactured across their source-book joins. Psalms retains canonical order for blocks/windows, while three-unit motifs may not cross a psalm boundary.

For the Aramaic-span sensitivity, masked language spans are hard gaps. Retained-language runs are never concatenated across those gaps.

## Interpretation

The reported quantities are descriptive measures of recurrence and sensitivity to spatial order. They are not calibrated as a poetry scale and do not by themselves establish genre, authorship, intentionality, or musical organization.

See `protocols/` for the complete frozen rules and `THIRD_PARTY_NOTICES.md` for source status.
