# Current cancellation cleanup measurement gap

Read-only source comparison: base `6f4a288d25343defd56b2dacdf596d1d89307e41` to head `a946b4288e396944bac329ae0a0ab44705f781c5`, plus the retained #7805 candidate files at the base commit. No source or test execution was performed for this note.

## Finding

The measured V12 path loses the active actuation identity specifically when the owner thread initiates cleanup itself. In `research/live_control/input_owner_v12.py`, `release(reason)` sets `release_pending`, calls `measurement.clear()` (lines 401–406), and only then releases keys by iterating `held` through `release_key` (lines 407–416). The measurement ledger's `clear()` empties its active key-to-identity map (`research/live_control/key_edge_measurement_v1.py`, lines 18–20). The subsequent `owner_release` record contains aggregate key release attempts and key intervals, but no per-key physical measurement or actuation identity (V12 lines 415–429).

This is reachable without an explicit `up_batch`: the owner loop detects an expired lease, cancellation, or changed focus and calls `release(...)` directly (V12 lines 488–508). Therefore a held key can be physically released and neutral state checked, while the cleanup receipt cannot prove which admitted actuation it released. V12 also does not retain the V39 event `(id, step)` context in `KeyEdgeMeasurements`; the current active tuple is only `(key, token, identity)` (`key_edge_measurement_v1.py`, lines 38–44). Even preserving the ledger through cleanup would need that context (or a trustworthy join at the bridge) to attribute the cleanup UP to the originating event.

This is separate from explicit batched UP after cancellation. The latter still goes through `up_batch` and the measured V4/V3 path: V4 joins `owner_explicit_keyup` records and copies a nested `physical_key_measurement` to the ordinary transition (V4 lines 123–150 and 96–118); the batch backend preserves those transitions. Retained full-05/full-06 runs show those explicit batch pairs, while their standard ordinary-release projection is incomplete because cancellation makes `ordinary_release_candidate` false. Those observations do not cover the independent owner-thread `release(reason)` route above.

## Comparison with #7805 prior art

The retained V13 candidate already has the needed owner-local hold identity shape: `_HoldIdentity` retains intent token, key, actuation ID, and event context (candidate lines 51–80). Its `release(reason)` samples each held key before and after KeyRelease/XSync, retires the held identity only on a confirmed UP, and records per-key `input_release_measurement` rows under `owner_release.per_key_release_measurements` (candidate lines 287–353). It appends that record before aggregate pointer/keymap verification, so a later aggregate-query failure does not erase the per-key attempt. The V2 bridge drains these owner cleanup rows in `execute`'s `finally` and again at the `release_all` barrier (bridge lines 14–44 and 68–80), covering cleanup that races the first drain.

The smallest reusable mechanism is the **stable hold identity plus event context**, the per-key cleanup bracket, and unconditional draining of owner cleanup records at both execution exit and the release barrier. The V13 files are research candidates based on the older A01 bridge; they are not compatible replacements for current measured V12/V4/V3 without integration work.

## Integration boundary

Keep owner-triggered cleanup as a distinct cleanup measurement event. Do not forge an `input_release_transition`, ordinary batch receipt, or ordinary-release candidate: the cancellation cleanup is not the normal ordered `up_batch`, and the current projector applies different acceptance requirements to those evidence types (`map01_overlap_controller_v39.py`, lines 867–910 and 1077–1086). A safe current-path adaptation should preserve identity/context before the release, record each cleanup attempt and its physical keymap bracket even if later aggregate verification fails, mark authority and application consumption false, and publish it through a cleanup-specific event consumed by an explicit cleanup projection. Missing identity, unknown samples, request/sync errors, or unverified release must remain unconfirmed and must not pair with a prior admission as a confirmed UP.

No claim here concerns live control, physical application consumption, or task outcome. The gap is source-derived; the retained full-run explicit-batch evidence demonstrates a different route only.
