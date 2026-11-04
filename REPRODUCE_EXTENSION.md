# Reproducing the poetic-comparator extension

This extension is deliberately separate from the frozen twelve-work article workflow. Run it from the repository root with Python 3.12+.

## Windows

```text
run\RUN_EXTENSION.bat
```

## Any platform

```text
python src/analysis/poetic_extension.py
python src/analysis/extension_summary.py
python src/analysis/validate_extension.py
```

No network access is required. Psalms, Job, and Song of Songs are stored under `sources/extension/biblical/` with pinned provenance. Runtime checkpoints are written only under `.local/extension_checkpoints/`; they are ignored by Git and are not part of the release archive. A checkpoint is reused only when its analysis signature matches the current code, protocol, and extension source files.

## Outputs

- `results/extension/poetic_comparator_inventory.csv` — source/corpus inventory for Psalms, Job, and Song of Songs.
- `poetic_coverage.csv`, `poetic_distance.csv`, `poetic_spatial.csv` — full fixed exact/expanded grids for the three preselected poetic comparators.
- `different_surface_coverage.csv`, `different_surface_spatial.csv` — exact-mode surface-host sensitivity for the ten distributed release corpora plus the three poetic comparators.
- `fifteen_work_primary_summary.csv` — compact primary-settings summary combining the existing twelve works with the three poetic comparators.
- `different_surface_primary_summary.csv` — compact primary-settings summary of the surface-host sensitivity.
- `extension_validation.json` — source/output hashes and frozen design metadata.

Detailed definitions and exclusions are in `protocols/poetic_comparator_extension.md`.

## Validation

`validate_extension.py` checks the frozen corpus inventory, completeness of the new grids, monotonicity of the surface-host subtraction, exact recovery of the existing ten-corpus baseline (120 coverage cells and 90 spatial cells), and hashes of all bundled extension CSV outputs.

The extension does not modify `results/comparison/`, the three published figures, `reference/`, or `config/published_outputs.json`.
