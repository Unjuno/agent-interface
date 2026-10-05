# Issue #59 A03 — paired-epoch ammo-aware cover guard

## Outcome

`PASS_PAIRED_EPOCH_FAIL_CLOSED` for the construction gate. Ten cases preserved coherent positive ammo (including the 1-unit boundary), and requested a new decision on zero ammo, health below floor, split sequence, split capture time, mismatched binding, Boolean/float sequence aliases, and unknown ammo. The independent auditor reconstructed every pair decision and per-signal guard result: 44/44 checks passed.

This extends A02's composed-guard prototype with the missing common-epoch requirement. It remains a standalone construction helper; no current v39 controller or production runtime file changed.

## Reproducibility

- Frozen main: `e561b25b700680df4e6ffd2b92faf1dde1682ef7`.
- Source and input identities: `FREEZE.json`; hashes checked before the one probe invocation.
- Probe and independent audit each ran once; retries 0; live allocation 0.
- Commands: `PYTHONPATH=research/live_control python3 -B research/doom/v39_ammo_cover_pair_guard_59_a03_20261005/probe.py` and then `python3 -B research/doom/v39_ammo_cover_pair_guard_59_a03_20261005/audit.py`.
- CPython 3.14.5, macOS arm64, stdlib-only monitor module; no container or isolation/resource-enforcement claim. A01's retained OrbStack cached-blob stop was not retried.
- `SHA256SUMS` covers freeze, fixture, source, result, and audit.

## Limits and next gate

No live typed frame, controller, fire cover, model wait, cancellation, key release, survival, useful effect, or MAP01 outcome was observed. Pair validation does not prove the runtime emits coherent paired frames or that a combined invalidation reaches the active-cover cancel path. The next required step is reviewed integration with regressions in the current controller, followed by a separately assigned live lane measuring ammo-change-to-invalidation-to-verified-empty-release and task progress. Do not infer authorization from this PASS.
