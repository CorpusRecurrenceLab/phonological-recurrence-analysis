# Aramaic-span sensitivity protocol

The full-stream analysis remains primary. The language-layer analysis is named **Aramaic-span exclusion sensitivity** because its purpose is to test dependence on the declared Aramaic spans, not to posit that recurrence should be limited to Hebrew.

A complementary **Aramaic-only descriptive check** applies the identical frozen geometry to the declared Aramaic spans themselves where sufficient material exists. No smaller parameter is introduced for a short run.

## Declared masks

The exact masks are frozen in `config/aramaic_masks.json`: Genesis 31:47 tokens 4-5; Jeremiah 10:11; Daniel 2:4 token 5 through 7:28; Ezra 4:8-6:18 and 7:12-26. They contain 4,829 words / 25,727 sound units.

## Hard-gap semantics

A masked interval is a true computational gap. Each contiguous retained-language run is analyzed separately. No motif, 64-unit window, coverage/distance block, 8-word fragment, 128-word evaluation block, or permutation may cross a language gap. The fixed offset/phase grid restarts at the beginning of each contiguous run. Eligible complete blocks are then pooled without changing geometry.

The rule is symmetric: exclusion treats Aramaic as gaps in retained Hebrew runs; the Aramaic-only check treats Hebrew as gaps in retained Aramaic runs.

## Geometry and reporting

Coverage, distance, exact/expanded matching, fragment sizes, radii, shuffle scopes, and 19 seeds are identical to the primary analysis. Only Genesis, Jeremiah, Daniel, and Ezra are recomputed for exclusion; the other 35 source-books are unchanged. Ezra-Nehemiah reporting pools recomputed Ezra with unchanged Nehemiah without creating cross-source motifs.

Aramaic-only values remain `NA` wherever the unchanged frozen geometry cannot be formed.
