# V39 legacy-transition A04 evidence rescue

## H / T / D / C / U

- **H:** A legacy `input_release_transition` row carrying nested V39 adapter-UP evidence must not be ignored while a separate `input_release_measurement` UP row keeps adapter intervals paired.
- **T:** Preserve the exact A04 WSLc candidate/baseline outputs, result, original 14-check audit, pinned baseline source, and byte-identical snapshots of the candidate source, test source, and input event fixture from source commit `af2ba4249a9f282f6b7c3fa3e0cca68c077aaa63`. Run the recovery-only hash/provenance auditor; do not rerun the experiment.
- **D:** The retained baseline fails one of two tests on the duplicate legacy-transition mutation; the retained candidate passes both tests and both mutations produce an incomplete receipt with null timing. The saved independent audit reports 14 checks and no errors. Recovery audit passes only if all 12 original manifest entries and the three source snapshots match their recorded SHA-256 values.
- **C:** This is archival recovery and integrity verification, not a new experiment. The original result and output bytes are copied unchanged; source/test/fixture snapshots make their historical hashes checkable without depending on the abandoned branch.
- **U:** One synthetic retained X-adapter event pair and deterministic projector only. No live X server, physical dwell, application consumption, task effect, threat response, recovery, or MAP01 outcome is established.

## Provenance and disposition

Recovered from the post-close tip of branch `test/59-v39-adapter-edge-cardinality-a01-20261005` (source commit above), after closed PR #7681. Its open successor #7690 preserves later A05–A08 work but does not contain this A04 result. This package has a separate additive path so the successor's files and manifest are not edited.

The original WSLc execution used pinned image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, `--pull never`, `--network none`, one requested CPU, 512 MiB requested memory, UID/GID 1000, read-only source, and a distinct writable output. Its recorded cgroup/swap warning is retained; full memory enforcement is not claimed.

`audit_recovered_a04.py` verifies saved provenance and hashes only. It does not execute the candidate or upgrade the experiment's scientific scope.
