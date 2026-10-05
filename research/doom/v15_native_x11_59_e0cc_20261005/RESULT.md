# Native measured V15 input-release construction — PASS within scope

On 2026-10-05 at 11:57:08–11:57:09 UTC, one ordinary construction invocation ran the actual measured V15 backend and V12/V4 owner chain against a fresh private Xvfb server. Both predefined cases passed. The independent raw reconstruction passed **658/658 logical checks**, and **8/8 raw-only negative controls** were rejected. These counts are assertions and mutations, not independent trials or estimates of reliability. No candidate replay was needed.

The executed source is PR #8094 head `2b0cb591c3ebcb84d1db983612613850c08fffea`. All 81 exported blobs matched the Git-bound inventory before the run and again afterward; 32 source modules were loaded. This package adds evidence only; it does not change any of those runtime or test blobs.

| Case | Observed behavior | Decision |
|---|---|---|
| Ordered multi-key UP | Real X-server keymap changed from neutral to a/s/w down. The focused window received DOWN a/s/w and UP w/s/a. Three distinct DOWN identities matched three complete ordered batch UP receipts, with shared sample brackets. Final tested keys were up. | PASS for this native backend component |
| Cleanup-first cancellation | A finite lease admitted a/s, then its cancel event was set. Owner cleanup produced verified UP measurements with the original identities and `per_key_cleanup_snapshot`. The later same-lease s/a batch raised `Cancelled`, added no observed key event or owner record, and retained two incomplete nonauthoritative rows. | PASS for this native backend component |

Both owner threads stopped and retained verified empty `close` records. The observer closed, Xvfb exited 0, and a post-run process check found no remaining Xvfb. The owned VM was stopped and read back as stopped at 11:58:16 UTC. The stopped VM and raw evidence remain preserved. Other VMs and the shared Docker daemon were not altered.

## Execution and evidence

- `PROTOCOL.md`: pre-execution H/T/D/C/U gates, finite cases, boundaries, and stop conditions. `PLAN.md` retains resource/duplicate reasoning.
- `freeze.json`: driver, auditor, protocol, package inventory and source-lock hashes before execution. `vm-freeze-verification.json` verifies the transferred bytes. `source-lock.json` binds paths to Git blobs and SHA256 hashes.
- `native_probe.py.txt`: byte-identical executed driver. `prepare_and_run.py.txt`: one-run host orchestration and exact systemd properties. `run-01-request.json` and `run-01-result.json`: requested invocation and completed exit 0.
- `run-01/raw.json`: native keymap, test-window events, admissions, owner/backend receipts, source hashes and shutdown state. SHA256 `923d7ce368cafe7a05b0799d7dbcac5eb39462628099d571c9d2cc4d8d8e3aa6`.
- `audit_native.py.txt` and `run-01/audit.json`: pre-frozen auditor and independent reconstruction. `audit_mutations.py.txt` and `run-01/audit-mutations.json`: post-run corruption controls on in-memory raw copies; original raw unchanged.
- `peer-native-review.md`: separate coauthor read-only reconstruction; no material inconsistency found. This is not a nonauthor quorum vote or merge authorization.
- `REPRODUCE.md`: safe read-only audit and explicit source reconstruction. Scripts are stored inertly to avoid accidental broad test collection.

## Environment and retained setup history

A new isolated OrbStack Debian 12 bookworm arm64 VM ran real Python-Xlib 0.33, Xvfb/X.Org 21.1.7, and Python 3.11.2. The candidate ran as non-root UID 501. Its actual cgroup readback was one CPU (`100000 100000`), 1 GiB RAM, zero swap allowance, and 64 tasks. The unit requested a 60-second limit, private network/tmp namespaces, read-only filesystem with one writable output subtree, and a 250 MiB per-file limit. Actual raw plus audit/negative-control files totaled 233,230 bytes. The complete installed package inventory is retained.

Cgroup values and namespace/interface identities were read back; no overload stress test or network-egress attack was performed. Source hashes remained unchanged; there is no separate read-only-mount penetration test. Resource controls are bounded execution safeguards, not research performance findings.

The existing shared Docker image inventory and a direct native-image inspect failed with content-store `operation not supported`, while metadata/version reads worked. No daemon restart, prune, foreign machine reuse or consumed allocation retry was attempted. The new VM succeeded. Before any candidate run, static review repaired driver-only Xlib API, wrapper traversal, partial-result retention, close-reason and cgroup-path mistakes. The original draft is retained as `native_probe-draft0.py.txt`; it was never executed. No setup or runtime failure has been relabelled as a candidate PASS.

## Scope, adoption and unresolved work

This reduces the uncertainty left by the earlier fake-X owner/child evidence: the current measured backend's multi-key batch and cleanup-first identity path work in these two small cases against a real **virtual X11 server**. It supports retaining the proposed implementation for further integration review. It does not establish error probabilities or justify a performance claim.

The driver uses the actual backend constructor and raw/release-batch methods, directly sets a program/step context, and uses a bounded `ProbeLease`. The interrupted case directly calls the backend's error-row helpers after the expected exception. It does **not** invoke production `execute`, V39, Session orchestration, a game, HUD capture, planner/model, physical display/keyboard or hardware input. XTEST delivery to the test window is not game/application consumption or useful task feedback. Source fields named `CONFIRMED_PHYSICAL_UP` refer here only to the conservative X-server keymap bracket, not hardware timing. No fresh live-game authorization, game result, task effect, recovery effectiveness, latency saving, Windows result, or full native-controller composition is established.

The earlier macOS fake-X V39 child evidence remains a separate component of the evidence chain; combining it with this Linux native component check does not create an unexecuted end-to-end native result. #59's live lane remains unassigned. No main update or PR merge was performed. Full PR review and the FINAL-v5 nonauthor/serialized integration conditions remain outstanding.
