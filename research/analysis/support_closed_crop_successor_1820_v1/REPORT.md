# Issue #2060 successor — support-closed crop reuse

## H/T/D/C/U

- **H:** Crop context is safe only when a current full-source support check proves exactly one target globally; otherwise emit RAW_FALLBACK or UNKNOWN.
- **T:** Freeze unique target, outside duplicate, target removed, inside ambiguity, and stale crop/source cases. Compare support-closure decisions with the oracle.
- **D:** experiment.py, five case rows, decision ledger, stale/source IDs, and SHA-256 digest.
- **C:** Unique current target yields CONTEXT_READY; duplicate, removed, or ambiguous targets yield RAW_FALLBACK; stale source/crop yields UNKNOWN; no input authority is generated.
- **U:** Model target selection, matcher false positives/negatives, package-size benefit, full-source check cost, latency, and GUI correctness remain unknown.
- **STOP:** One finite standard-library support-closure fixture; no model, GUI, network, runtime, or user input.

## Result

Command: python experiment.py

- Unique target: CONTEXT_READY.
- Outside duplicate, removed target, and inside ambiguity: RAW_FALLBACK.
- Stale source/crop identity: UNKNOWN.
- Result digest: db6d49f3d786e89b05fe8ea88fd210da528d7c35133b5dcd5a37af0a47d63d51.

**Decision: PASS_SUPPORT_CLOSED_CROP_FALLBACK_SCOPED.**

This verifies the support-closure safety boundary only. It makes no model, packaging-benefit, matcher-quality, latency, or GUI claim.
