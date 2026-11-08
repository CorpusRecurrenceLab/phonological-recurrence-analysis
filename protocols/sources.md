# Corpus and source protocol

## Fixed comparison set

The study uses twelve fixed works. They are comparison cases, not representative samples of all Biblical Hebrew, Modern Hebrew prose, or Hebrew poetry.

| Repository key | Work | Role | Reading source |
|---|---|---|---|
| `Genesis`–`Deuteronomy` | Pentateuch | Primary corpus | Sefaria, `Tanach with Ta'amei Hamikra` |
| `Joshua`, `Judges` | Joshua, Judges | Other Biblical comparison | same Sefaria version |
| `modern_523` | Yosef Haim Brenner, *Mikan u-mikan* | modern prose / novel | frozen Dicta-Nakdan prepared layer |
| `modern_7924` | Ahad Ha-Am, *Shilton ha-sekhel* | modern prose / essay | frozen Dicta-Nakdan prepared layer |
| `modern_884` | Shaul Tchernichovsky, *Hatunata shel Elka* | modern poetic idyll | source vocalization |
| `rivlin_ali_baba` | Hebrew *Ali Baba* narrative associated with Rivlin | modern narrative comparison | source vocalization; reacquired from Project Ben-Yehuda |
| `bialik_beir_haharegah` | H. N. Bialik, *Be-ir ha-haregah* | modern poem | source vocalization; reacquired from Project Ben-Yehuda |

Psalms, Job, and Proverbs are not included in the fixed twelve-work comparison. The study therefore does not present that comparison as a genre-discrimination test. The distinct poetic-comparator control evaluates Psalms, Job, and Song of Songs without altering the twelve-work comparison; see `poetic_comparators.md`.

## Biblical material

The Biblical source is the frozen Hebrew Sefaria version `Tanach with Ta'amei Hamikra` (source metadata: tanach.us). Sefaria identifies this version as Public Domain. The repository stores the verse-level source strings used by the project. Preparation selects explicitly marked qere, removes only recognized source scaffolding, preserves verse order, and records the deterministic transformation. Unknown markup stops preparation.

## Modern material

The three distributed modern works are pinned Project Ben-Yehuda study inputs. Brenner and Ahad Ha-Am use the exact machine-vocalized prepared layers that entered the study; Tchernichovsky uses source vocalization. Raw Dicta API responses are not required for study reproduction and are not distributed.

The two additional Project Ben-Yehuda works are not redistributed as complete texts. `src/additional_sources.py` downloads their pinned pages, extracts the `actualtext` body while excluding site apparatus, applies the declared Bialik colophon exclusion, and verifies the expected extracted-text hashes in `config/additional_sources.json`. A changed upstream text is rejected rather than silently substituted.

## Qamats-qatan asymmetry

The frozen Biblical files contain no U+05C7 QAMATS QATAN codepoints. Consequently, Biblical U+05B8 is encoded uniformly as `a`, including forms traditionally read with /o/. The frozen Dicta-prepared layers contain explicit U+05C7 in some modern material. This representational asymmetry is quantified in the data and quantified by the targeted lexical `kol` sensitivity diagnostic. The diagnostic is not a general qamats-qatan resolver.
