# Issue #59 A02 — composed health/ammo cover guard

## Outcome

`PASS_DUAL_SIGNAL_FAIL_CLOSED` for the construction gate. A wrapper composing two instances of the current-main generic observable guard preserved the notional fire cover at ammo=4 and at the positive boundary ammo=1, and requested a new decision for ammo=0, unknown ammo, a non-advancing ammo sequence, an ammo binding mismatch, and health below its authored floor. The independent reference audit passed 24/24 checks.

This is a small viable construction for the A01 gap, not an integrated v39 fix. The controller still wires the live cover monitor to health only. No persistent runtime semantics, cancellation, physical release, or behavior was changed.

## Reproducibility

- Frozen current-main source: `research/live_control/observable_signal_guard_v2.py` at base `109cedcf1fafc150e235c91141eb47bbc7396b43`.
- Source and fixture hashes: `FREEZE.json`; all verified before execution.
- One probe and one independent auditor invocation; live allocations 0; retries 0.
- Commands: `PYTHONPATH=research/live_control python3 -B research/doom/v39_ammo_cover_guard_59_a02_20261005/probe.py`; then `python3 -B research/doom/v39_ammo_cover_guard_59_a02_20261005/audit.py`.
- CPython 3.14.5 on macOS arm64, stdlib-only. No container or isolation claim; A01's read-only OrbStack image inventory failure was not retried.
- Hashes for freeze, fixture, prototype, result, and audit are in `SHA256SUMS`.

## Limits and next gate

The wrapper assumes that health and ammo rows refer to one observation epoch; it checks each guard's source binding/sequence but does not implement a paired typed-frame join or controller event delivery. It also does not measure whether zero ammo is observed before a cover renewal, whether a running fire action cancels promptly, whether key release is verified, or whether task progress improves. Before any live allocation, review a regression-backed implementation of pair identity and combined invalidation in the current runtime, then obtain the separately assigned lane required by Issue #59.
