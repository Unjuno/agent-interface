# Issue #57 next gates — 2026-11-21

## Current state

Issue [#57](https://github.com/Unjuno/agent-interface/issues/57) remains open.
It requires an integrated matched token/latency/correctness comparison,
standard-caller task success after recovery, repeated reliability, and trusted
fresh allocation custody. The completed work in this wave does not satisfy
those gates.

## Ordered research gates

1. **Fresh setup-only successor to #908.** The prior #908 first outcome is
   consumed `HOLD_ASSET_MATERIALIZATION_UNAVAILABLE`; do not reopen or rerun
   that study. A successor must use the pinned exact Mindustry v160.2 JAR
   (87,022,576 bytes; SHA-256
   `7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539`) and
   canonical save (Git blob `7663b25633d853a257fbb407723fe85579120111`, 23,335
   bytes; the older smoke records content SHA-256
   `8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed`). It
   must be zero-model, no controller input, disposable/private, and retain raw
   readiness, oracle, process, hash, and cleanup evidence. The canonical save
   is on current main; the JAR still needs exact materialization and checksum
   verification.
2. **Resource lane for #5130.** Issue
   [#5130](https://github.com/Unjuno/agent-interface/issues/5130) requests one
   serial Docker Desktop CPU-only slot and explicitly forbids starting,
   building, pulling, inspecting, or altering containers until a named
   coordinator/owner grants that lane and sibling-container ownership is
   reconciled. User permission to use this PC does not constitute that
   allocation attestation. Issue
   [#7924](https://github.com/Unjuno/agent-interface/issues/7924) retains
   WSLc client/container ownership as STOP/UNKNOWN. No Docker/WSLc operation was
   performed in this wave.
3. **One frozen Mindustry economics allocation.** Only after gates 1–2,
   preserve #1679 semantics: plain/ephemeral/persistent, six fixed tasks, one
   allocation, no retry/replacement/tuning, all model-attempt usage, exact
   correctness and lifecycle evidence, and independent raw-only audit. The
   existing #908 result is setup evidence only; the historical #2624 V2
   archive is reported incomplete. Do not claim setup readiness from the
   preregistration alone.
4. **Standard caller and recovery.** Keep the recovered-task success and
   repeated reliability tests separate from Mindustry economics. A single
   successful Edge form POST or one R281 input effect does not close either.
5. **Product boundary.** Retain the Windows portable-runtime result as scoped
   packaging evidence. Public distribution, Linux/WSL startup, live input, and
   side-effect authorization remain separate acceptance checks.

## PR #10340 gate

The rebased PR head is `c47ae761ed7a8c47e6d5d6b16937b468145956cd`; all five
GitHub checks passed. Its prospective journal is non-dispatching and does not
connect an external allocation attestor. The archived Edge smoke is one local
form task with an offline model double, not a matched comparison. The journal
suite was reproduced in a complete temporary source tree against current-main
pinned sources: 13/13 pass normally and 13/13 pass under `-O` on Windows
Python 3.11.9. An earlier incomplete-tree attempt produced 3 passes / 10
source-lookup errors; those errors were setup omissions, not code failures.
The local pass establishes the synthetic journal composition only. It does
not supply trusted external allocation custody, enable dispatch, or establish
provider/live comparison results. Keep PR #10340 draft until those broader
gates are separately satisfied.

The test and source SHA-256 values, pinned main SHA, runner commands, and
temporary tree location are recorded in
[`pr10340-lineage-correction-20261121.md`](pr10340-lineage-correction-20261121.md).

## Disposition

Keep #57 and #5130 open. Keep #908/#879 as consumed historical evidence; do
not overwrite their STOP/HOLD records. Reconcile and advance one dependency
gate at a time, preserving failed/held outcomes.
