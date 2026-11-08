# Fragment-preserving spatial control

This control asks whether changing the neighborhood of the **same lexical material** changes local phonological coverage.

Each original segment is divided into nonoverlapping fragments of eight complete words. Sixteen fragments form a 128-word evaluation block. Incomplete final material is omitted and retention is reported. Mixed-triplet motifs crossing an eight-word fragment boundary are excluded in both the observed and rearranged conditions; matches may connect different fragments within the same evaluation block.

The fixed radius set is 32, 64, and 128 sound units. The study emphasizes radius 64.

For each corpus, 19 deterministic permutations use seeds 2026102601–2026102619 under three scopes:

1. `local128`: shuffle the sixteen fragments within each evaluation block;
2. `regional1024`: shuffle within groups of up to eight consecutive evaluation blocks of the same segment;
3. `whole_corpus`: shuffle all eligible fragments within the corpus, then evaluate them in the same number of 128-word blocks.

Every eligible fragment is used exactly once in each permutation. The observed-minus-null difference is descriptive; permutation ranges are not confidence intervals and no permutation p-value is claimed.

Because exact words, morphology, formulae, names, syntax, and topic-related recurrence remain present, the control does not isolate a uniquely poetic mechanism. It tests the contribution of received spatial arrangement while holding the fragment inventory fixed.
## Surface-word sensitivity

The main fragment-preserving control deliberately retains exact words. A separate exact-mode surface-word control requires qualifying motif tokens to have different complete phonological surface-word hosts. It is defined in `poetic_comparators.md` and does not replace the control above.
