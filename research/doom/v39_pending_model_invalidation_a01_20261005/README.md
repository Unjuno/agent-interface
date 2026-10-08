# V39 pending-model invalidation construction A01

## Result

`PASS_CONSTRUCTION_SCOPED` on attempt A04. The literal `while not future.done()` loop and following planner-result assignment from the frozen V39 controller were executed with the production paired-signal monitor, cancellation helper, and final-admission helper. Three deterministic schedules ran in the cached WSLc image; a separate network-disabled container audited the raw result and source/script hashes with zero errors.

- Hard health change (100 to 89; authored hard minimum 90): while the planner future was pending, the guard invalidated; the controller requested planner interruption, emitted cover cancellation, received an empty-release receipt, then observed a late answer and rejected it as `REJECTED_POLICY_INVALIDATED`.
- Unknown health/ammo binding: while pending, the pair mismatch failed closed; the same interrupt/cancel/verified-release order preceded late answer rejection.
- Soft health change (100 to 95; maximum loss 10): the guard preserved the existing policy; the late answer was left `READY_FOR_ACTION_VALIDITY`, with no interrupt/cancel and no input authority.

Attempt A01 stopped before candidate execution because the container could not resolve the Windows worktree `.git` pointer. A02 reached final admission but failed on a malformed fake monotonic timestamp. A03 reached the expected control sequence but the test fake double-recorded one terminal receipt. All three first outcomes and their freezes are retained under `attempts/`; A04 used a distinct output directory. No source/runtime code changed.

## Scope

This only verifies controller ordering under fabricated observations and a fabricated pending future. It does not show that real threat-linked HUD changes cross the authored guard, that the HUD reader extracts health/ammo accurately, or that cancellation occurs quickly enough. It does not measure a real provider, GUI/X11, physical input release, useful feedback, recovery benefit, ammo/progress, or MAP01 completion. The monotonic timestamps in the synthetic monitor are execution receipts, not latency results.

Current direction r139 requires a fresh live threat exposure. The private game lane is unassigned, so this construction result does not satisfy that gate or authorize a live run. Issue #59 remains open.

## Reproduction

The recorded invocation was `python research/doom/v39_pending_model_invalidation_a01_20261005/run.py`. The runner verifies the frozen repository commit, implementation hashes, and cached image ID, then runs the candidate and independent auditor in separate WSLc containers with `--pull never`, network disabled, one CPU, and a read-only source mount. It refuses to overwrite the retained first result; any later run needs a new attempt ID, freeze, and output path. See `FREEZE.json`, `PROTOCOL.md`, and `results/pending-loop-a04/`.

The candidate JSON carries the internal schema label `construction-a03`, inherited from the preceding construction harness revision. Attempt identity is A04 in the frozen input, command names, output path, and receipts; the captured candidate output is unchanged.

