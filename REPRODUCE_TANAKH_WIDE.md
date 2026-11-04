# Reproducing the full-Tanakh extension

The full-Tanakh analysis is embedded as a self-contained frozen release under `extensions/tanakh_wide/`. It extends, rather than replaces, the baseline and poetic-comparator analyses.

## Windows

From the repository root:

```text
run\RUN_TANAKH_WIDE.bat
```

## Any platform

```text
python extensions/tanakh_wide/project.py all
```

The first run downloads the 39 frozen source JSON files from the exact pinned public Git commit, verifies each Git blob id, prepares the reading stream, runs the complete fixed parameter grids, runs the Aramaic-span sensitivity, and validates the frozen outputs. To reuse a verified source cache without network access:

```text
python extensions/tanakh_wide/project.py all --offline
```

Static release validation requires no network access:

```text
python extensions/tanakh_wide/project.py verify
```

The extension's own README and protocols document the source freeze, source exceptions, 39-source-book / 24-book reporting rule, Psalms boundary rule, fixed geometries, permutation seeds, and Aramaic-span hard-gap sensitivity.

## Cross-layer continuity

Run:

```text
python src/analysis/validate_integration.py
```

This verifies that the shared computational core is byte-identical and that the ten Biblical books present before the full-Tanakh expansion reproduce the same frozen primary coverage, distance, and local-spatial values.
