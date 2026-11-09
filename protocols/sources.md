# Corpus and source protocol

## Current corpus and reporting units

The primary analysis covers **all 39 pinned biblical source-book files**, representing the **24 traditional books of the Tanakh** for reporting, together with **five selected Modern Hebrew comparison works**. Computation treats each of the 39 source books separately; no motifs are created across source-book boundaries. The modern texts form a deliberately heterogeneous reference set, not a matched or representative genre sample. See `README.md`, `THIRD_PARTY_NOTICES.md`, and `results/comparison/tanakh_and_modern_44_work_descriptive.csv`.

A historical **twelve-work comparison component** is retained for reproducibility. Its twelve items are the five Pentateuchal books, Joshua, Judges, and the five modern comparison works. It is a component of the current 39+5 study, **not** the extent of the present biblical corpus.

| Repository key | Work | Role in twelve-work component | Reading source |
|---|---|---|---|
| `Genesis`–`Deuteronomy` | Pentateuch | Biblical comparison | Sefaria, `Tanach with Ta'amei Hamikra` |
| `Joshua`, `Judges` | Joshua, Judges | Biblical comparison | same Sefaria version |
| `modern_523` | Yosef Haim Brenner, *Mikan u-mikan* | modern novel | fixed Dicta/Nakdan-assisted prepared reading |
| `modern_7924` | Ahad Ha-Am, *Shilton ha-sekhel* | modern essay | fixed Dicta/Nakdan-assisted prepared reading |
| `modern_884` | Shaul Tchernichovsky, *Hatunata shel Elka* | modern poetic idyll | original source vocalization |
| `rivlin_ali_baba` | Yosef Yoel Rivlin, Hebrew *Ali Baba* translation | modern narrative | source vocalization; permission-restricted full text |
| `bialik_beir_haharegah` | H. N. Bialik, *Be-ir ha-haregah* | modern poem | included public-domain extracted source |

The current primary analysis also includes Psalms, Job, Proverbs and the other pinned biblical source books. Psalms, Job and Song of Songs were additionally investigated by the *poetic-comparator control*; see `poetic_comparators.md`. Neither historical comparison component establishes genre-specificity.

## Biblical material

The Biblical source is the frozen Hebrew Sefaria version `Tanach with Ta'amei Hamikra` (source metadata: tanach.us). Sefaria identifies this version as Public Domain. The repository stores the 39 verse-level source files used by the project. Preparation selects explicitly marked qere, removes only recognized source scaffolding, preserves verse order, and records deterministic transformations. Unknown markup stops preparation. The full 39-book source freeze, hashes and mirror revision are described in `THIRD_PARTY_NOTICES.md` and configuration files.

## Modern material and distribution

The three primary modern sources are distributed as frozen study inputs. Brenner and Ahad Ha-Am use the Nakdan-assisted prepared layers that entered the study; Tchernichovsky uses source vocalization. Raw Dicta API responses are not required and are not distributed. Bialik's complete frozen extracted text **is included** under its provider-indicated public-domain status. Rivlin's permission-restricted text **is not included**. `src/additional_sources.py` can acquire/recheck the pinned provider page or check a locally supplied authorized HTML file, applying source exclusions and recorded hashes. A changed upstream text is rejected rather than silently substituted. See `protocols/acquisition.md` and `THIRD_PARTY_NOTICES.md`.

## Qamats-qatan asymmetry

The frozen Biblical files contain no U+05C7 QAMATS QATAN codepoints. Consequently, Biblical U+05B8 is encoded uniformly as `a`, including forms traditionally read with /o/. Some frozen Dicta-prepared modern material contains explicit U+05C7. This representational asymmetry is quantified in the data and tested by the targeted lexical `kol` sensitivity diagnostic. The diagnostic is not a general qamats-qatan resolver.
