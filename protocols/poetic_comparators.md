# Poetic comparators and different-surface-word control

## Status and scope

This is a fixed control using the same computational settings as the twelve-work comparison, not a poetry classifier. The designated Biblical poetic comparators are: **Psalms, Job, and Song of Songs**. Their results are retained regardless of direction.

The computational representation, mixed-triplet definition, direct consonant substitutions, block geometry, radii, distance geometry, fragment size, rearrangement scopes, and permutation seeds are unchanged from the main protocols.

## Sources

All three books use Sefaria's Hebrew **Tanach with Ta'amei Hamikra**, whose source metadata identifies `tanach.us` and a Public Domain license.

Psalms is copied from the project's September 2026 frozen Sefaria download. Job and Song of Songs are stored from the same Sefaria export/version through the pinned public mirror `Sivan22/Sefaria-Export-Hebrew-Texts`, commit `0f41148df41c0fe47321a7da7c01390b7ad7e872`. As a source-equivalence check performed before analysis, the mirror Psalms text matched the project freeze at 150 chapters, 2,527 verses, 359,088 UTF-8 bytes for the newline-joined verse stream, and FNV-1a-64 `1d7cbbdd2a2812c6`.

The source JSON files are distributed in `sources/variants/biblical/`, so the comparison is reproducible offline.

## Psalms boundary rule

Psalms is treated as one canonical ordered stream for block and distance geometry. This avoids discarding short psalms merely because a psalm is shorter than an analysis block. A mixed triplet is nevertheless **forbidden to cross a psalm boundary**. Blocks and 64-unit windows may include material from two neighboring psalms, but no motif token is constructed from sound units belonging to both.

Job and Song of Songs are each treated as one canonical book stream; no chapter boundary is introduced as an analytical break.

## Different-surface-word control

The lexical sensitivity is exact-mode only and leaves the transcription and motif definition unchanged. Each motif token receives a **phonological surface host** from the full wordform(s) that contain its three sound units:

- a motif wholly inside one word is hosted by that complete phonological wordform;
- a motif spanning a word boundary is hosted by the ordered tuple of complete phonological wordforms it touches.

A motif recurrence qualifies in the `different_surface_word` condition only when the two motif tokens have different hosts. Thus an exact repeated wordform cannot by itself create a qualifying recurrence, while the same three-unit sound motif can still recur in different wordforms. This is deliberately a surface-form control: it is **not** lemmatization, stemming, morpheme stripping, or a claim to remove all lexical/grammatical cohesion.

The control is applied to the complete fixed coverage grid (512/1,280 units; offsets 0/half; radii 32/64/128) and to the fragment-preserving spatial control at all three radii. It is not imposed on the set-based distance statistic because that statistic collapses motif tokens to motif types inside each 64-unit window and therefore has no token-host identity without defining a new estimand.

This historical comparison component contains word-control results for ten core corpora plus Psalms, Job, and Song of Songs. The current primary different-host analysis covers all 39 Tanakh source books. The two additional modern works (`rivlin_ali_baba`, `bialik_beir_haharegah`) were not included in this sensitivity. Bialik’s public-domain source is distributed; its exclusion is an analytical scope decision, not a source-availability restriction. Rivlin’s permission-restricted source is not redistributed. No completed five-work modern different-host comparison is claimed. See `tanakh/different_surface_word.md`.

## Outputs

Control outputs are located under `results/controls/`. The twelve-work study tables, figures, regression fixtures, and `config/published_outputs.json` remain unchanged.

## Exploratory passage inspection

`examples/close_reading_selection.json` records an earlier inspection set of 36 passages historically labelled “weak cases” and ten passages sampled without reference to detector score. The labels are exploratory provenance, not validated outcome categories. This list is not used as confirmatory evidence or to define the complete-Tanakh corpus. The source data and selection record are retained unchanged.
