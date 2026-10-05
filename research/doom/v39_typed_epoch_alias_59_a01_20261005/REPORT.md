# V39 typed epoch alias A01 — result

## Result

**FAIL_CLOSED_EPOCH_IDENTITY_GAP.** On exact source from current `main` `e561b25b700680df4e6ffd2b92faf1dde1682ef7`, the integer control produced a snapshot. All eight malformed reader rows also produced snapshots: Boolean and float values aliasing the expected integer in `sequence` and `capture_ns`, tested separately for both required `health` and `ammo` signals. The independent raw-only audit reconstructed the nine cases and their expected actual-pipeline outcomes.

## Meaning

`extract_typed_observation` compacts the reader rows without exact type checks for the row epoch fields. `build_action_snapshot` compares those fields to the enclosing epoch with equality. In Python, `True == 1` and `1.0 == 1`, so malformed row metadata is accepted as belonging to the current observation. The selected snapshot then contains the enclosing integer epoch and the reader's health/ammo value.

This establishes a source-boundary contract defect under the supplied reader inputs. It does not establish that the in-tree WAD readers emit malformed metadata; those readers may always copy validated integer metadata. No game, model, GUI, OS input, live allocation, or action authority was used.

## Evidence and reproduction

- Candidate: 9 cases, exit 0; the experiment classification is a fail-open boundary finding, not a runner failure.
- Independent auditor: 53/53 checks, exit 0, reconstructing all eight aliases as source-accepted and contract-invalid.
- Inputs, exact source bytes, blob IDs, pre-execution freeze, audit freeze, stdout/stderr, exit statuses, and checksums are retained in this directory.
- Host: CPython 3.12.14, macOS arm64, Pillow 12.3.0. No container/isolation claim. The prior OrbStack image-inventory failure was not retried.

Commands are in `RUN.md`. The source-identifying manifest is `FREEZE.json` and `SOURCE_MAP.json`; `AUDIT_FREEZE.json` binds the independent audit inputs.

## Decision and next gate

A regression-backed repair should enforce exact integer type and value for every required signal row's `sequence` and `capture_ns` before the action snapshot can be emitted, then run the malformed controls as negatives. This experiment does not itself modify production code. Issue #59's live threat exposure, per-key up/release timing, independently useful feedback, bounded recovery, and a separately labelled MAP01 attempt remain outstanding and still require their own assigned live allocation.

## Exploratory pre-freeze note

Before A01 was frozen, one ad hoc read-only probe had already tested a health row with Boolean `sequence` and Boolean `capture_ns` aliases against the then-current `origin/main` `6822c1396cd9530c3313d4f41d251f7b8724d87b`; both were accepted. That probe was not preregistered, its raw output was not retained as a package artifact, and it is not counted as an A01 invocation or result. A01 is frozen against the subsequent `e561b25b700680df4e6ffd2b92faf1dde1682ef7` and expands the scope to both health/ammo, Boolean/float aliases, and an independent audit. The overlap and retention limitation are disclosed rather than treating the exploratory output as formal evidence.

## Interpretation-label correction

The original freeze and candidate result use the wrong label `FAIL_CLOSED_EPOCH_IDENTITY_GAP`. The raw rows show eight malformed aliases accepted; the corrected interpretation is `FAIL_OPEN_EPOCH_IDENTITY_GAP`. The independent audit label is consistent with that reading. The original freeze, preregistration and raw result remain unchanged; no candidate or auditor rerun occurred. Full correction and hash anchors: [CORRECTION.md](CORRECTION.md) and [CORRECTED_INTERPRETATION.json](CORRECTED_INTERPRETATION.json). Treat the label mismatch as a protocol defect.
