# Reproducing the article

Run from the repository root with Python 3.12+.

## Full workflow

```text
python -m pip install -r requirements.txt
python reproduce_article.py
```

The first full rebuild requires network access for two non-redistributed Project Ben-Yehuda works. All other frozen study inputs are included. The extended acquisition step verifies the expected extracted-text hashes and stops on mismatch.

## Article-output mapping

### Table 1: reference coverage

`results/comparison/coverage.csv`

Filter: `block=512`, `offset=0`, `radius=64`. Both `exact` and `expanded` modes are reported.

### Table 2: distance contrast

`results/comparison/distance.csv`

Filter: `cap=1024`; for each corpus/mode average the four `offset × phase` differences between `gap=0` and `gap=1024`.

### Table 3: fragment-preserving rearrangement

`results/comparison/spatial.csv`

Filter: `radius=64`; report `delta = observed - null_mean` for `local128`, `regional1024`, and `whole_corpus`, in both modes.

### Appendix A: corpus size and retention

`results/article_corpus_inventory.csv`

The file is regenerated directly from newly built sound streams and comparison outputs. It does not read a previous copy of itself.

### Appendix B: fixed rearrangement example

`results/worked_example.json`

The example uses the first eligible Genesis 128-word block and the first prespecified local permutation. It is illustrative, not an additional inferential test.

### Verse-level presence statements

`results/verse_presence.csv` is the article-facing summary. During core analysis, the verse map and summary are rebuilt under the ignored intermediate path `results/analysis/` and checked against `reference/verse_map.json` and `reference/verse_summary.json`. The denominator is the number of verse records in the frozen Sefaria API segmentation used by this project.

### Qamats-qatan sensitivity

`results/qamats_kol_sensitivity.csv`

This targeted diagnostic recodes only lexical כָּל that the frozen Biblical encoding represents as `k-a-l`; it is not a general qamats-qatan resolver.

### Supplementary representative examples

`results/representative_examples.json`

For the ten locally available comparison corpora, the high-density case is selected mechanically from `results/comparison/density.csv` as the first complete 512-unit block attaining the maximum exact R64 coverage. Rivlin and Bialik use the disclosed fixed-opening rule because their complete source texts are not redistributed.

### Figures

- Figure 1: `figures/figure1_distance.*`
- Figure 2: `figures/figure2_density.*`
- Figure 3: `figures/figure3_rearrangement.*`

The figure script is `src/analysis/comparison_figures.py`; it reads only the comparison CSVs.

## Validation

`python project.py verify` verifies the release manifest. `python project.py prepare` rebuilds the ten distributed sound streams and requires exact equality with `reference/segments.json`. The unit suite includes brute-force checks of expanded matching and exact coverage, 90 direct verse-map checks, and fragment-boundary controls. The full workflow also validates exact-mode regression against frozen fixtures and checks that expanded values are supersets of exact values on identical material.

Runtime validation records are written under `.local/validation/` and are not part of the published scientific results.
