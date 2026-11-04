# Primary Tanakh-wide analysis protocol

The primary analysis is computed on the complete frozen Masoretic reading stream, including the declared Biblical-Aramaic spans. No poetry/prose label enters computation or book selection.

## Mixed-triplet motif

A motif is a contiguous sequence of three atomic sound units containing at least one vowel and at least one consonant. For local coverage, two occurrences qualify only when their start positions are at least 3 units apart and no more than the fixed radius apart.

Two modes are retained symmetrically: **exact** identity and **expanded** identity or exactly one direct consonant substitution from the frozen set in `transcription.md`.

## Coverage

Block lengths are 512 and 1280 sound units; offsets are 0 and half-block; radii are 32, 64, and 128. Incomplete tails are omitted and retention is reported. The primary coverage readout is 512 / offset 0 / radius 64.

## Distance

Motifs are represented in 64-unit windows. Exact similarity uses set Dice. Expanded similarity uses maximum-cardinality one-to-one matching of distinct motif types connected by identity or one allowed direct substitution, normalized as `2M/(|A|+|B|)`.

Maximum gaps 256, 1024, and 4096 use analysis blocks 512, 1280, and 4352. Offsets are 0/half and phases 0/64. The primary distance readout is adjacent-minus-gap-1024 at cap 1024, averaged equally across the four offset/phase condition means. If all four cannot be formed, the primary value is `NA`.

## Fragment-preserving spatial control

The source-book is divided into nonoverlapping fragments of 8 complete words; 16 fragments form a 128-word evaluation block. Motifs cannot cross an 8-word fragment boundary. For each corpus, 19 deterministic Python `Random` seeds 2026102601-2026102619 are used under `local128`, `regional1024`, and `whole_corpus` shuffle scopes. Every eligible fragment is used exactly once per permutation. The primary spatial readout is observed minus mean permuted coverage at radius 64.

## Traditional 24-book reporting

The 39 source-books are authoritative computational units. Multi-source traditional books are reporting aggregations only. Coverage pools complete source-book blocks by block count; distance pools each fixed condition by eligible source-book block count and then averages the four pooled condition means; spatial deltas are weighted by retained sound units. No artificial join creates motifs.

## Fixed-grid integrity

`config/primary_expected.json` freezes every source-book primary result plus a full-grid FNV-1a-64 audit fingerprint. `src/primary.py` recomputes the complete grids and validates the primary values before writing generated outputs.
