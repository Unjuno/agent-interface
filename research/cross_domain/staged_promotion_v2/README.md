# Staged promotion v2

Scoped cross-domain research successor to Issue #271 v1.

Each attempt writes to a unique stage. Retry B is generation 2 and is published to one canonical path immediately after its exact stage completes. A later predecessor A callback is generation 1. The `naive` arm publishes any completed stage; the `generation_gate` arm publishes only the current generation. Both start B without waiting for A to reap.

Frozen v2 result: naive final A 8/8; generation gate final B 8/8; actual B reap precedes A reap 16/16; physical XTEST Return releases verified. See `REPORT.md` and `result.json`.

The previous v1 allocation is not relabelled: it remains incomplete 14/16 because the frozen harness treated a valid absent predecessor stage as a failure. V2 changes only absent-stage handling (`NO_EFFECT`).

Binary FFmpeg fixtures and complete per-case evidence are retained in the conversation archive, not byte-completely in GitHub. Their SHA-256 identities were frozen before measurement in `FREEZE.json` and `plan.json`. Do not rerun consumed case IDs.
