# Comparison scopes and reporting limitations

## Three distinct corpus scopes

1. **Fixed comparison set:** seven Biblical books (the Pentateuch, Joshua, Judges) and five Modern Hebrew comparison works. The fixed comparison set uses the declared pinned source variants and prepared-reading layers.
2. **Poetic-comparator and surface-word control:** Psalms, Job, and Song of Songs, using the same fixed motif and geometry definitions. The original exact-mode `different_surface_word` sensitivity covers **13** designated corpora. A separately verified application of the same method to **all 39 Tanakh source-books** is provided in `results/tanakh/word_control/` and `protocols/tanakh/different_surface_word.md`. The three modern works with available word-host streams can be compared descriptively; two additional modern works have no comparable word-host sensitivity.
3. **Complete Tanakh:** all **39** pinned source-books, with **24** traditional reporting categories. These source-books are evaluated separately; multi-source traditional books are reporting aggregations, not concatenated sound streams. The primary analysis includes Biblical Aramaic; Aramaic-exclusion and Aramaic-only checks are sensitivity analyses.

The ten earlier Biblical source files in `sources/variants/biblical/` are regression fixtures, not duplicates that may replace the pinned `sources/original/tanakh/` edition. Their byte hashes are intentionally different. Use `python run/tanakh.py sources` to check the physical 39-book source set and `python run/reproduce_all.py` for the full computation.

## Modern Hebrew comparison set

The five modern works are not five genre-matched prose controls. They contain varied genres, including Bialik's poem *Be-ir ha-Haregah* and Rivlin's translated *Ali Baba*. They provide literary reference points, **not** a single exchangeable random sample of modern prose. Group or genre claims require appropriate control selection and uncertainty estimation. Nakdan-assisted reading layers are frozen inputs and cannot be assumed to match a fresh invocation of the service.

In `results/comparison/tanakh_and_modern_44_work_descriptive.csv`, the ten mode rows of the modern group have unpopulated `words`/`sound_units` values. This is an explicit reporting limitation of that cross-scope table, **not** evidence that their processing failed. Do not infer sizes from that table. The two non-applicable fixed-gap distance cells for Obadiah are `NA`, **not zero**: fixed geometry is not resized or filled for short books.

## Metric interpretation

The computational unit is an atomic sound token, not a Python character in its romanized spelling: `sh`, for example, is a single sound unit. Exact triplets must be identical; expanded matching allows the narrowly specified one-step consonantal substitution, but no vowel changes or arbitrary transitive closure. Refer to `transcription.md` and `tanakh/transcription.md` for the frozen conversions.

Coverage, distance, and fragment-preserving rearrangement quantify different properties of recurrence. They are **not** calibrated as poetry probabilities or a score of intentional composition. The data support tests of order-sensitive sound recurrence in received, vocalized texts; they do not independently establish authorship, deliberate design, historical date, a specific metre, a recoverable melody, or any proposed interpretation of cantillation as musical notation.

Avoid treating dozens of book-by-setting cells as independent replications, using short-book `NA` as zeros, or claiming universal dominance over all modern texts. More specific claims require effect sizes and appropriate inferential controls, including lexical/morphological confounds.

## Publication policy

Keep the frozen comparison, controls, and complete-Tanakh tables distinct from regenerated working summaries. Recomputed outputs and validation logs go to `.local/`; do not overwrite frozen tables to improve their apparent agreement. The repository is a computational research record, not by itself a final inferential verdict on the broader poetic-musical hypothesis.
