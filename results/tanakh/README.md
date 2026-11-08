# Frozen result tables

`primary/source_books_39.csv` is the authoritative 39-source-book primary summary. `primary/traditional_books_24.csv` is the reporting aggregation to the traditional 24 books; it never represents text concatenation.

`sensitivity/exclusion_source_books_39.csv` and `sensitivity/exclusion_traditional_books_24.csv` report the hard-gap Aramaic-span exclusion sensitivity. `sensitivity/affected_primary_vs_exclusion.csv` isolates the four affected source-books. `sensitivity/aramaic_only_descriptive.csv` reports the declared Aramaic spans on their own where the unchanged geometry is feasible.

The complete parameter grids are regenerated under `.local/tanakh/` by the executable analysis. Full-grid audit fingerprints are frozen in `config/tanakh/primary_expected.json` and `config/tanakh/aramaic_sensitivity_expected.json`.
