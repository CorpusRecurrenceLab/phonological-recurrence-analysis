# Acquisition and vocalization

## Fixed-source reproduction

The public package is designed so that the ten-work core can be reproduced without network access or credentials. Biblical readings are rebuilt from the frozen Sefaria Hebrew source projection and verified against the included prepared layer. The three primary modern works use the exact frozen prepared reading layers that entered the study. Raw Dicta API response payloads are deliberately not distributed and are not required by `python run/project.py prepare`.

The two additional comparison works (Rivlin and Bialik) are not redistributed as full texts. Rebuilding the twelve-work comparison from first principles therefore requires network access to their pinned public pages; the acquisition code verifies the expected content hashes and fails if the remote content has changed.

## Fresh Dicta/Nakdan candidate acquisition

A fresh service run is optional and separate from study reproduction. Candidate files are written under `.local/nakdan/`, which is excluded from Git, and never silently replace the frozen inputs.

Dicta API access requires the user's own authorization. The workflow accepts the service endpoint from the provider instructions and reads a personal key from the environment or hidden input. Keys must never be stored in committed files or command-line arguments. Provider attribution appears in the repository README and accompanying source documentation.

Fresh service output is a new candidate reading, not a guarantee of byte-for-byte identity with the pinned reading layer. It must be reviewed and explicitly promoted outside the reproduction path before it can be used in a new study version.
