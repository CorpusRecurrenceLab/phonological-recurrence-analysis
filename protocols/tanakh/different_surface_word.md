# Tanakh-wide different-surface-word sensitivity

## Scope and interpretive limit

This is a **secondary exact-mode robustness analysis** covering all 39 frozen Sefaria source books. The same control is also applied to a separately declared 13-corpus comparison set; the complete-Tanakh and 13-corpus calculations retain their own fixed geometries and units. Reporting groups of 24 traditional books are metadata; the computation is performed separately on all 39 original book streams. The method is a comparison of sound-recurrence statistics, **not** a poetry classifier, a morpheme-controlled analysis, a test of melodic transcription, or a reconstruction of historical intention.

## Fixed data and representation

The original vocalized source JSONs, reading exceptions, and the canonical phonological core are reused from `config/tanakh/`, `src/tanakh/prepare.py`, `src/tanakh/primary.py`, and `src/analysis/poetic_comparators.py`. Do not change equivalence rules, transcriptions, book boundaries, or exceptional qere/ketiv readings for this sensitivity. Each mixed three-unit motif consists of one or two vowel units and the remaining consonant units. Each occurrence retains its position and **complete surface-word host**. If it spans a word boundary, its host is the ordered tuple of the complete phonological surface words it touches. In the different-surface condition, the same exact motif can match only occurrences with unequal hosts; repeated identical wordforms alone do not qualify. This does not exclude shared morphemes, cognate wordforms, roots, morphological endings, or formulaic construction.

Psalms is treated as one ordered book stream for fixed analysis windows, but no triplet motif may span a boundary between consecutive psalms. A word-boundary index is used to implement this rule. All other books remain single streams and are not concatenated across books. The primary form of the analysis includes Aramaic passages as supplied by the source; the previously existing separate Aramaic-exclusion sensitivity belongs to the main Tanakh layer and is not silently transferred to this new control.

## Coverage and spatial statistic

For the 39-book coverage summary, the prespecified comparison uses exact three-unit motifs, fixed windows of 512 sound units, offset 0, and radius 64. The general implementation also supports windows 512/1,280, offsets zero/half, and radii 32/64/128. The reported coverage is the fraction of sound positions included in qualifying motif tokens (not a proportion of words). The coverage reduction compares identical algorithmic conditions with and without the host-inequality restriction.

For spatial analysis, the procedure forms eight-word fragments, retains complete 128-word blocks (16 fragments), and computes sound-position coverage at radii 32/64/128. Observed order is compared to 19 seeded rearrangements (`2026102601 + replicate_index`) at three fixed scales: within 128-word blocks (`local128`), 1,024-word regions (`regional1024`), and whole-book (`whole_corpus`). Difference `delta = observed - mean(rearranged)`. The reported result is a descriptive effect size, usually converted to percentage points. The 19 replicates are insufficient for robust corpus-by-corpus significance testing or broad multiple-comparison claims.

A book may yield only a few complete 128-word blocks. This is not repaired by stretching or joining it with other books. For length-sensitive interpretation, report complete 128-word blocks and explicitly distinguish books with fewer than eight. Avoid interpreting `NA` as zero when other fixed geometries are not applicable.

## Verification, regeneration and publication status

The recorded tables are:

- `results/tanakh/word_control/different_surface_coverage_summary.csv` (39 rows)
- `results/tanakh/word_control/different_surface_spatial.csv` (702 rows)
- `results/tanakh/word_control/different_surface_spatial_replicates.csv` (13,338 rows)

Check their internal consistency and agreement with pinned primary and comparator data using:

```
python run/tanakh_word_control.py --verify
```

Perform a separate source-to-result recalculation without overwriting the frozen reference tables using:

```
python run/tanakh_word_control.py --recompute
```

This more expensive operation saves resumable per-book checkpoints under `.local/word_control_checkpoints/`, writes aggregated output into `.local/word_control_recomputed/`, and compares every calculated cell with the included tables. Per-book checkpoints are accepted only when the pinned source, the active calculation code, the applicable reading rules, and the frozen manifest fingerprint are unchanged. Local edits to calculation code therefore invalidate prior checkpoints even before the manifest is updated. To smoke-test the recalculation of one book, use `--recompute --book Obadiah`. The 39-book recalculation was performed in the research workspace; the packaged full-recompute command should be independently re-run on the target operating system before release.

## Modern Hebrew comparability

For *this particular different-surface-word sensitivity*, three modern works are available in `results/controls/`. The different-host calculation was not performed for the two additional modern works (`rivlin_ali_baba`, `bialik_beir_haharegah`), which must **not** be counted as completed controls. Bialik’s public-domain source is included; the missing analysis is a scope decision, not a redistribution restriction. Rivlin’s source remains permission-restricted. The three available modern works also differ substantially in size and retained fragment fraction. The comparison of 39 Bible books with three modern works is descriptive and unweighted: books are not independent random observations, genre and chronology are confounded, and neither medians nor positive direction alone establishes poetic design. Full morphological or lexical-matching controls remain an additional research question.
