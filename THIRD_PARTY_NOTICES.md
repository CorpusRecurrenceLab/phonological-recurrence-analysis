# Third-party sources and tools

This repository contains or processes material from third-party sources. The MIT license applies only to original project code and documentation.

## Biblical Hebrew and Aramaic

The Biblical study layers use Sefaria's Hebrew version **Tanach with Ta'amei Hamikra**, whose source metadata identifies tanach.us. Sefaria identifies this version as **Public Domain**.

The comparison repository distributes the frozen Biblical source projections used in the earlier comparison layer. The full-Tanakh analysis freezes all 39 Sefaria source-books through the pinned public mirror `Sivan22/Sefaria-Export-Hebrew-Texts`, commit `0f41148df41c0fe47321a7da7c01390b7ad7e872`, and records the exact Git blob id of every source JSON. Its preparation script rejects any source whose blob differs from the frozen manifest.

## Project Ben-Yehuda

The Modern Hebrew comparison works were obtained from Project Ben-Yehuda. The repository retains the three study inputs that are distributed with the comparison release and cites Project Ben-Yehuda as their digital source. Bialik's *Be-ir ha-haregah* is marked **public domain** on its Project Ben-Yehuda entry and its frozen extracted text is included under `sources/original/modern/` with source attribution. Rivlin's Hebrew translation of *Ali Baba and the Forty Thieves* (1978) is marked **permission-only** (*mugash bi-reshut pirsum*) and is **not redistributed**. Its HTML is retrieved from the original provider only when needed, or supplied under `.local/additional/` by an authorized reader; the extracted text is checked against the frozen SHA-256. The MIT license does not apply to third-party texts.

Project Ben-Yehuda's terms distinguish public-domain works from works made available only with permission. Users of redistributed source texts remain responsible for respecting the status shown by the source provider.

## Dicta Nakdan

The frozen prepared layers for Brenner and Ahad Ha-Am were produced during the study with Dicta's Nakdan. Raw API responses, credentials, and service keys are not distributed. The comparison reproduction workflow uses the frozen prepared layers and does not contact Dicta.

Shmidman, A., Shmidman, S., Koppel, M. and Goldberg, Y. (2020), 'Nakdan: Professional Hebrew Diacritizer', *Proceedings of ACL: System Demonstrations*, 197–203. https://doi.org/10.18653/v1/2020.acl-demos.23

The Dicta logo in `assets/dicta-logo.png` is included for required provider attribution and is not covered by the MIT license. Fresh API use requires the user’s own authorization and personal non-transferable credentials.
