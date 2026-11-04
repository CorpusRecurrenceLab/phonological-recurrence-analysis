# Core analysis protocol

## Mixed-triplet motif

A motif is a contiguous sequence of three atomic sound units containing at least one vowel and at least one consonant. Within an analysis segment, motif occurrences are indexed by start position.

For coverage at radius `R`, two occurrences qualify when their starts are at least 3 units apart and no more than `R` units apart. Coverage is the fraction of sound positions covered by one or more qualifying occurrences; overlapping coverage is counted once.

The article reports exact identity and a restricted expanded mode defined in `transcription.md`.

## Coverage grid

Block lengths: 512 and 1,280 units. Offsets: 0 and half a block. Radii: 32, 64, and 128 units. Incomplete segment tails are excluded and retention is reported.

The article's reference coverage table uses block 512, offset 0, radius 64.

## Distance analysis

Motifs are represented in 64-unit windows. Similarity is evaluated for adjacent windows and increasing gaps. Exact similarity uses set Dice. Expanded similarity uses maximum-cardinality one-to-one matching of distinct motif types connected by identity or one permitted direct substitution, normalized as `2M/(|A|+|B|)`.

Maximum gaps 256, 1,024, and 4,096 use analysis blocks 512, 1,280, and 4,352 units respectively. Offsets 0/half and phases 0/64 are retained. The article's primary distance summary uses the adjacent-minus-gap-1,024 contrast averaged across four offset/phase conditions.

## Verse-level presence

The Pentateuchal verse map projects local motif participation onto the verse records in the frozen Sefaria source. It is a presence diagnostic, not verse-level density: one qualifying link and many qualifying links both count as positive. The denominator is the number of verse records in the frozen source segmentation used by this project, not a universal claim about Masoretic verse totals.

## Validation

The release compares rebuilt exact-mode results with immutable regression fixtures. Independent tests also check exact and expanded coverage by brute force, maximum matching by exhaustive search on small motif sets, 90 direct verse-map cases (5 books × 3 verses × 3 radii × 2 modes), and the prohibition on motifs crossing fragment boundaries.

A successful technical validation means that the declared computation reproduced its frozen reference. It is not a linguistic certification of every machine vocalization and does not imply a required scientific direction.
