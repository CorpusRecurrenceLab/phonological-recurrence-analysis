# Regression fixtures

These files are immutable expected outputs from the frozen exact-mode analysis. They are used only to detect accidental changes in preparation or analysis code.

- `segments.json` and `readings.json`: expected ten-corpus prepared streams.
- `matched.json`: exact distance-analysis fixture.
- `coverage_matched_512.json` and `coverage_matched_1280.json`: exact coverage fixtures.
- `coverage_matched_*_reading_sensitivity.json`: fixed six-reading sensitivity fixtures.
- `verse_map.json` and `verse_summary.json`: Pentateuchal verse-presence fixtures.

A match to a fixture establishes computational reproducibility under the declared rules; it is not independent evidence for the literary interpretation.
