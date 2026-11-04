# Phonological Recurrence Analysis

Reproducibility repository for a sequence of fixed analyses of order-sensitive phonological recurrence in Biblical and Modern Hebrew. The project has expanded in scope without replacing its earlier study layers. The same frozen computational core is retained throughout.

## Study layers

### 1. Baseline comparison

The original reproducibility layer compares Genesis, Exodus, Leviticus, Numbers, Deuteronomy, Joshua, and Judges with five fixed Modern Hebrew comparison works. It includes:

- frozen Biblical and distributed Modern Hebrew source material;
- the prepared reading layers actually used in the study, including Nakdan-assisted layers where declared;
- exact and restricted-expanded mixed-triplet analyses;
- coverage, distance, and fragment-preserving spatial controls;
- qamats/readings sensitivities, verse maps, worked examples, regression fixtures, and article-facing figures;
- deterministic tests and validation.

The two Modern Hebrew works that are not redistributed in full are reacquired from pinned Project Ben-Yehuda pages and hash-checked before use.

### 2. Poetic-comparator and different-surface-word extension

A frozen robustness extension adds Psalms, Job, and Song of Songs under the same analysis geometry. It also includes the exact-mode `different_surface_word` control, which requires recurrent motif tokens to occur in different complete phonological surface-word hosts. This removes recurrence attributable solely to repetition of the same complete surface wordform without claiming to remove all lexical or morphological cohesion.

See `REPRODUCE_EXTENSION.md` and `protocols/poetic_comparator_extension.md`.

### 3. Full Tanakh extension

`extensions/tanakh_wide/` extends the unchanged engine to all **39 Sefaria source-books**, reported also as the traditional **24 books of the Tanakh**. No Biblical book is selected or removed by genre or by result. The primary calculation retains the full declared Masoretic reading stream, including Biblical Aramaic. A separate hard-gap Aramaic-span exclusion sensitivity and an Aramaic-only descriptive check test language-layer dependence without altering the primary corpus.

The full-Tanakh extension freezes the source mirror commit and exact Git blob for every source book. It keeps the same motif definition, correspondence rules, block geometry, radii, distance geometry, fragment size, three rearrangement scopes, and nineteen deterministic permutation seeds used by the earlier work.

A cross-layer regression check confirms that the ten Biblical books already present in the earlier layers (Genesis–Judges, Psalms, Job, and Song of Songs) reproduce the same primary coverage, distance, and local-spatial values in the full-Tanakh run.

See `REPRODUCE_TANAKH_WIDE.md`.

## Shared computational core

The following frozen files are common to the study lineage:

- `src/core/phonetic_core_v2.py`
- `src/core/perpetual_qere.py`
- `src/preparation/prepare_biblical_reading.py`

The self-contained Tanakh-wide extension carries byte-identical copies of these three files so that its frozen release can be executed independently. `src/analysis/validate_integration.py` checks this identity and the overlap of primary results.

## Quick validation

From the repository root with Python 3.12+:

```text
python project.py verify
python -m unittest discover -s tests -v
python src/analysis/validate_extension.py
python src/analysis/validate_integration.py
python extensions/tanakh_wide/project.py verify
python -m unittest discover -s extensions/tanakh_wide/tests -v
```

On Windows, launchers are provided in `run/`.

## Reproducing the baseline article workflow

Install the figure dependency and run:

```text
python -m pip install -r requirements.txt
python reproduce_article.py
```

See `REPRODUCE_ARTICLE.md`. The baseline figures under `figures/` and the tables under `results/comparison/` are retained as frozen outputs of that comparison layer; they are not silently rewritten to represent the later Tanakh-wide scope.

## Reproducing the poetic-comparator extension

```text
run\RUN_EXTENSION.bat
```

or:

```text
python src/analysis/poetic_extension.py
python src/analysis/extension_summary.py
python src/analysis/validate_extension.py
```

## Reproducing the full-Tanakh extension

```text
run\RUN_TANAKH_WIDE.bat
```

The first run acquires the 39 public-domain Sefaria source JSON files from the pinned public mirror and verifies each Git blob before analysis. Subsequent runs may reuse the verified local cache offline. Full instructions are in `REPRODUCE_TANAKH_WIDE.md`.

## Repository layout

- `sources/` — frozen inputs and prepared reading layers from the baseline and poetic-comparator work.
- `config/` — baseline corpus/source manifests and frozen metadata.
- `src/` — baseline preparation, analysis, extensions, validation, and figure code.
- `reference/` — immutable regression fixtures for the baseline analysis.
- `results/comparison/` — frozen baseline comparison tables.
- `results/extension/` — frozen poetic-comparator and different-surface-word outputs.
- `figures/` — frozen baseline article figures.
- `examples/` — provenance for the baseline close-reading inspection set.
- `extensions/tanakh_wide/` — self-contained full-Tanakh source manifest, protocols, code, frozen result tables, and language-layer sensitivity.
- `tests/` — baseline and extension tests.
- `run/` — Windows launchers.

## Interpretation boundary

The measurements describe recurrence abundance, proximity, and sensitivity to textual order. They are not calibrated as a poetry score and do not by themselves establish genre, authorship, intentionality, metre, melody, or a unique historical performance practice. The repository preserves both supportive and countervailing comparisons rather than selecting texts or parameters to recover a preferred ranking.

## Source and licensing notes

See `THIRD_PARTY_NOTICES.md` and the full-Tanakh source protocol under `extensions/tanakh_wide/protocols/`. The MIT license applies to original project code and documentation; third-party texts retain their own status and terms.
