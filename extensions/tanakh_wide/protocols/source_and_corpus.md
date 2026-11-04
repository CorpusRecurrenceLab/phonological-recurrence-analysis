# Source and corpus protocol

## Corpus freeze

All 39 Sefaria source-books under Torah, Prophets, and Writings are included. They correspond to 24 traditional Tanakh books only at the reporting layer. No source-book is removed after results are inspected.

The source is `Tanach with Ta'amei Hamikra`, whose Sefaria metadata identifies tanach.us as the source and Public Domain as the license. The mirror repository, pinned commit, exact path, Git blob SHA-1, chapter count, and verse count for every source-book are frozen in `config/source_freeze.json`.

## Reading stream

For each verse, the frozen adapter selects bracketed qere in place of preceding ketiv, removes only recognized `(פ)`, `(ס)`, and `(׆)` source scaffolding, and fails on unknown source markup. Three perpetual-qere normalizations are handled by the frozen transcription core: *hi*, *Yerushalayim*, and *Yissakhar*.

Eight ketiv-without-qere cases are omitted only after exact reference, token-position, and surface-form validation (`config/ketiv_without_qere.json`). Two exact HTML-appended repeat tails, at Lamentations 5:22 and Ecclesiastes 12:14, are removed only if the frozen suffix matches `config/editorial_repeat_tails.json`. Any unexpected HTML remains an error.

Preparation of the pinned corpus yields 305,584 words and 1,602,109 computational sound units with zero unresolved tokens. Frozen per-book counts and adapter totals are in `config/preparation_expected.json`.

## Boundaries

The 39 source-books remain independent computational streams. Samuel, Kings, the Twelve, Ezra-Nehemiah, and Chronicles are not concatenated for motif creation. Psalms is kept in canonical order; analysis windows/blocks may span a psalm boundary, but a three-unit motif may not cross it.

Short books are not padded, resampled, or removed. Any impossible frozen geometry is `NA`.

## Biblical Aramaic

The primary corpus retains Biblical Aramaic. Explicit masks are frozen in `config/aramaic_masks.json`: Genesis 31:47 tokens 4-5; Jeremiah 10:11; Daniel 2:4 token 5 through 7:28; Ezra 4:8-6:18 and 7:12-26. These masks are used only in the separate hard-gap sensitivity described in `aramaic_sensitivity.md`.
