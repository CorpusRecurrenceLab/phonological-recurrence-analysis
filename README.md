# Phonological Recurrence Analysis

Public reproducibility repository for sound-pattern recurrence in the complete Hebrew Tanakh and selected Modern Hebrew comparison texts. The repository contains analysis code, declared source editions, phonological preparation rules, deterministic controls, fixed results and regression tests. It is independent of any particular publication.

## Corpora

- **Tanakh:** 39 pinned Sefaria source-book JSON files (`sources/original/tanakh/`), corresponding to 24 traditional books for reporting. The sound stream follows the declared Masoretic reading. Results use the 39 books as computational units; aggregations never manufacture cross-book motifs.
- **Modern Hebrew:** five fixed comparison works; three distributed primary sources and two additional works. The Bialik source is distributed under its public-domain designation. The permission-only Hebrew translation of *Ali Baba* by Yosef Yoel Rivlin is **not redistributed** and must be obtained by authorized readers separately. See `THIRD_PARTY_NOTICES.md`.
- **Source variants:** `sources/variants/` holds alternate pinned Biblical source projections required by specific fixed comparison calculations. These are scientific input variants, not additional books in the Tanakh count.
- **Prepared readings:** `sources/prepared/` contains pinned reading layers, including Dicta/Nakdan-assisted Modern Hebrew preparations. Recreating Nakdan output with a current service is optional and may produce a different version.

## Analyses

- Three-unit mixed-vowel/consonant sound recurrence, exact and declared restricted-expanded matching.
- Coverage, proximity/distance and fragment-preserving spatial rearrangement at fixed settings.
- Correspondence between different phonological surface-word hosts across 39 books, with coverage and spatial rearrangement controls.
- Fixed reading and qamats sensitivities, Psalms boundaries, and Biblical Aramaic-span hard-gap sensitivity.
- Modern comparison and named poetic-comparator grids, with separately specified sampling frames.

These are distinct measurements, **not** a calibrated poetry score or proof of authorship, historical metre or melody. The five modern comparators are not a balanced genre sample. See `protocols/`.

## Quick validation (no network or API key)

From the repository root, with Python 3.12+:

```text
python -m pip install -r requirements.txt
python run/verify_unified.py
python run/project.py verify
```

## Reproduce bundled sources offline

```text
python run/reproduce_offline.py
python run/project.py verify
```

This regenerates available source-to-result layers and checks the restricted Rivlin-dependent tables **only against frozen outputs**, without claiming to have rerun them from the restricted text.

## Complete source-to-result reproduction

Acquire the restricted Rivlin HTML from Project Ben-Yehuda under its applicable conditions, then supply it locally:

```bat
set "HASHIRA_RIVLIN_HTML=D:\path\to\rivlin.html"
python src/additional_sources.py --check --offline
python run/reproduce_all.py --offline
python run/project.py verify
```

The verified Bialik text and 39 Tanakh source JSONs are already included. Rivlin's extracted text must match the frozen SHA-256. Never commit the restricted source, generated `.local` files, credentials, or Nakdan API responses. No SSL-bypass is used.

For a separate source-to-result check of different-surface-word analyses (long-running):

```text
python run/tanakh_word_control.py --verify
python run/tanakh_word_control.py --recompute
```

## Structure

- `config/`: source freezes, reading exceptions, parameters and published hashes
- `sources/original/tanakh/`: 39 canonical source books
- `sources/variants/`: pinned alternative text representations used in explicitly scoped comparisons
- `sources/original/modern/`, `sources/prepared/`: source and reproducible reading layers
- `src/core/`, `src/preparation/`, `src/analysis/`, `src/tanakh/`: shared engine and analysis implementations
- `run/`: user-facing commands and Windows batch scripts
- `protocols/`: source, transcription, analysis and control definitions
- `results/`: frozen numerical outputs of each analysis type
- `reference/`: immutable numeric regression fixtures
- `tests/`: tests for computational and acquisition behavior

See `REPRODUCE.md` for command details and `THIRD_PARTY_NOTICES.md` for rights and attribution.

## Overview figures

The three overview visualizations can be regenerated directly from pinned result tables using `python src/analysis/overview_figures.py --out figures/overview`. The output is three RGB TIFF images (600 dpi). This utility is a visualization of released measurements and does not change analysis results.

## Dicta Nakdan acknowledgement

The prepared reading layers for Brenner and Ahad Ha-Am use Dicta Nakdan; see `THIRD_PARTY_NOTICES.md` for attribution and use conditions.

![Dicta logo](assets/dicta-logo.png)
