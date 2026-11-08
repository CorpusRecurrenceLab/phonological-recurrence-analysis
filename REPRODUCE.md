# Reproduction guide

## Check the fixed release

`python run/verify_unified.py` verifies published inputs, outputs, and invariants without fetching external sources. `python run/project.py verify` validates the content manifest.

## Recompute all bundled inputs offline

`python run/reproduce_offline.py` rebuilds the distributed comparison inputs, reruns the eligible core computations, prepares all 39 Tanakh source books, executes the full-Tanakh analysis, checks Aramaic sensitivity and the different-surface-word published table, and verifies source/fixture consistency. It does **not** claim to recompute Rivlin-dependent outputs without the separately licensed text.

## Recompute the full comparison with licensed input

Obtain the authorized Rivlin source yourself from `https://benyehuda.org/read/17705`; provide its HTML using `HASHIRA_RIVLIN_HTML`. Then run `python src/additional_sources.py --check --offline` and `python run/reproduce_all.py --offline`. The extracted text must match the pinned SHA-256.

## Different-surface-word source-to-result rerun

`python run/tanakh_word_control.py --recompute` recomputes 39-book outputs into `.local/` with resumable checkpoints. `--verify` checks frozen results, including 180 comparator-overlap and 117 primary regressions; it does not rerun the source data.

## Optional new Nakdan preparation

The pre-existing prepared reading layers are sufficient for the fixed analyses. Any new Dicta/Nakdan invocation uses the researcher's own key and writes candidate artifacts only in `.local/`. These must be reviewed separately and never silently replace frozen sources. The public license does not automatically apply to third-party prepared texts; consult `THIRD_PARTY_NOTICES.md`.

## Output safety

Generated diagnostics, checkpoints and caches belong in `.local/` and must not be committed. The final `python run/project.py verify` must pass after every full reproduction.
