# Current V39 release-batch versus archived A01 owner compatibility A01

Result: **FAIL_COMPATIBILITY** on exact main `7754ef4e268fcb5166ece66ad821ef1af57cabd6`. Current `doom_owner_thread_release_batch_backend_v1._flush_pending_ups()` calls `owner.call("up_batch", lease, keys)`. The archived A01 `InputOwner` was instantiated on an inert fake X display and rejects that same operation with `ValueError: unknown input operation`. Its worker and fake display closed cleanly, with zero XTest calls. Current `live_control/input_owner_v12.py` has an explicit `up_batch` path; matching `InputOwner` naming does not imply protocol compatibility.

This directly qualifies the post-repair A02 result: selecting the archived owner identity is not a valid fix by itself. A compatible adapter would have to preserve V39's pending-UP delivery order, per-batch owner-state sample and verified-empty cleanup while providing appropriately scoped per-key release evidence. This construction test does not design or validate that adapter.

The plan and frozen H/T/D/C/U gates are in `PLAN.json`; exact source hashes and sizes are in `source-manifest.json`. `run-01/` retains stdout, stderr, exit receipt and the first result. The independent readback verifies all source blobs and the result/receipt boundary.

No key-down was admitted. This is not a native input, X server, physical release, useful-feedback, task-effect, recovery, timing, threat-response or MAP01 result. Issue #59's live threat-exposure lane remains unassigned.

Reproduce using the frozen source snapshots and a fresh output directory:

```sh
python research/doom/v15_releasebatch_legacy_owner_compat_a01_20261005/run_compat.py /new/output/path
python research/doom/v15_releasebatch_legacy_owner_compat_a01_20261005/audit.py
```

## Follow-up against the already-frozen A04/A05 candidate

Current main's #7957 package adds A04, which stopped before either case because its test-only controller left the production V2 constructor owner as `None`; it did not measure per-program cleanup. `candidate_a05_unrun.py` and its independent auditor are corrected follow-up sources, but remain unrun. On this macOS host, even read-only `docker images --digests` failed with containerd `operation not supported` while opening the pinned image blob. No pull, daemon switch, or alternate image was attempted, so A05 remains **HOLD_INFRASTRUCTURE** and has no new raw result. Reopen only with a functioning authorized isolated container runtime, current-main source freeze, and one candidate plus independent audit; do not call A04's STOP a cleanup finding or A05 a result.
