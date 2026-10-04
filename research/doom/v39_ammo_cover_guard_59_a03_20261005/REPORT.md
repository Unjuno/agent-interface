# Issue #59 A03 — paired observation epoch boundary

## Result

The paired-frame construction probe passed all six frozen cases. The initial independent reference audit scored 25/26 because the oracle mislabeled a coherent zero-ammo row's top-level pair status; that audit is preserved as `AUDIT_INITIAL.json`. After correcting that oracle label, the second audit passed all 26 checks without rerunning the probe. Coherent positive health/ammo preserved policy. Each sequence, capture-time, or binding mismatch invalidated before either individual guard could preserve policy. A coherent zero-ammo pair also invalidated.

This closes the specific false-preserve case in the A02 synthetic composition: a positive ammo sample from sequence 2 can no longer be combined with healthy health from sequence 3. It does not establish that current runtime signals have a shared identity or can be paired this way.

## Provenance and limits

The guard source is current-main `research/live_control/observable_signal_guard_v2.py` at `e561b25b700680df4e6ffd2b92faf1dde1682ef7`; its frozen SHA-256 is recorded in `FREEZE.json`. Fixture, candidate, auditor, result, and audit hashes are recorded in `SHA256SUMS`. The successful probe ran once; the independent auditor ran once. A preliminary import-path invocation failed before execution and wrote no result; details are retained in `RUN.md`.

This is a synthetic construction result, not a v39 integration, typed-frame delivery, cancellation, key-release, game, model, GUI, task-effect, or performance result. It does not authorize a live allocation.
