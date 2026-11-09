# Acquisition and vocalization

## Fixed-source reproduction

The current primary study uses 39 source-book JSONs of the Tanakh and five selected Modern Hebrew comparators. The public package preserves the original 39 biblical source files and deterministic preparation logic, so its available source-to-result analyses can be verified offline. A historical seven-biblical-book/three-modern-work core remains reproducible without remote services or API credentials; it is **not** the full corpus definition. The first three modern comparison works use fixed prepared layers, including the Nakdan-assisted readings of Brenner and Ahad Ha-Am. Raw Dicta API payloads are not distributed and are not required by `python run/project.py prepare`.

Among the two additional modern works, **Bialik is distributed**: its frozen extracted text is present under `sources/original/modern/` with public-domain source attribution. **Rivlin is not distributed** as a complete text because its source is permission-restricted. Reproducing Rivlin-dependent outputs from source requires an authorized local HTML copy or lawful acquisition from the pinned Project Ben-Yehuda page. The acquisition code verifies recorded content hashes; it does not silently accept changes. The offline verification command checks frozen Rivlin-dependent outputs without claiming to have recomputed them from the unavailable full text. Consult `README.md`, `REPRODUCE.md`, `THIRD_PARTY_NOTICES.md` and `config/additional_sources.json`.

## Fresh Dicta/Nakdan candidate acquisition

A fresh service run is optional and separate from study reproduction. Candidate files are written under `.local/nakdan/`, which is excluded from Git, and never silently replace the frozen inputs.

Dicta API access requires the user's own authorization. The workflow accepts the service endpoint from the provider instructions and reads a personal key from the environment or hidden input. Keys must never be stored in committed files or command-line arguments. Provider attribution appears in the repository README and accompanying source documentation.

Fresh service output is a new candidate reading, not a guarantee of byte-for-byte identity with the pinned reading layer. It must be reviewed and explicitly promoted outside the reproduction path before it can be used in a new study version.
