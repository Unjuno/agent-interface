# Current disposition (append-only)

This file supplements, and does not modify, the historical A01/A02 reports or their frozen SHA-256 manifests.

- A01 is a synthetic source audit pinned to #7602 source commit `76886c5cc41ef801bf1d0cb153b1dabf444d9127`; its retained result found touching, overlapping, and reversed closed sampling intervals were accepted as paired by that exact projector. It makes no claim about live measurements.
- A02 is an independent synthetic source check pinned to #7602 source commit `40c6a278d06ec4411b72dd5d7d8899d85bebfcf4`; it verified strict DOWN-end-before-UP-start classification on the fixture and all 100 enumerated cases.
- A02's historical sentence saying “The PR remains draft” is stale. GitHub currently records #7602 as closed unmerged. Its description says the candidate scope was incorporated into successor #8065, which remains an open Draft at head `6591b5703862c73d375a6646374ad82a26505bcb`.
- As of main `19a6b723e58ccfd2b8265e88659589ef9223fcc9`, neither package directory exists. The package paths were also absent from changed-file lists for the inspected #7692 and #8065 proposals. This supplements the source-level provenance record only; it does not establish acceptance or execution of the successor implementation, or current runtime behavior.

No candidate, game, model, GUI, X server, or input allocation was run for this rescue. Frozen source snapshots, fixtures, reports, manifests, and saved JSON results are copied byte-for-byte; original files are not rewritten.
