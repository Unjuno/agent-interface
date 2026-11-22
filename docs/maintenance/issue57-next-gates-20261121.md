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
   readiness, oracle, process, hash, and cleanup evidence. Both canonical saves
   on current main match the pinned size/hash. The official JAR is now locally
   materialized and hash-verified, but Ubuntu WSL has no Java runtime; no game
   launch or formal smoke occurred. See the bounded
   [asset-readiness packet](../../research/integration/mindustry_asset_readiness_v1_20261121/RESULT.md).
   The current disposition is `HOLD_LAUNCH_RUNTIME_MISSING`; the setup smoke
   remains pending an available Java runtime.
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
4. **Standard caller and recovery.** R08 now reconstructs the complete retained
   no-provider fixture journal through the adapter repairs merged by PR #10451;
   public `task_success` remains null, and the run did not exercise expiry or
   recovery. Keep recovered-task success and
   repeated reliability tests separate from Mindustry economics. A single
   successful Edge form POST or one R281 input effect does not close either.
   R149 shows a recovered/released Win32 action can be followed by a real
   queued task effect 691 ms after the sampled neutral horizon. The
   [`post_authority_effect_attribution_v1`](../../research/integration/standard_mcp_task_ledger_57_v1/post_authority_effect_attribution_v1/RESULT.md)
   probe confirms the existing ledger collapses that case and an in-authority
   effect to the same `task_success=true`. Before counting recovered task
   success in a matched comparison, keep factual final-state score separate
   from effect timing and authority eligibility. The offline synthetic score
   receipt adapter is now composed with the reuse-horizon evaluator, and its
   current-main normal-completion path also accepts only generation-bound
   verified release/horizon custody. Neither establishes a live caller-to-score
   handoff: R08 has exact public result lookup and bracketing captures, but the
   recovered-task path still needs a fresh eligible standard-caller trial
   plus repeated reliability evidence. See the
   [normal-completion adapter packet](../../research/integration/standard_mcp_task_ledger_57_v1/completed_owner_handoff_r01_20261122/README.md).
5. **Product boundary.** Retain Windows and Ubuntu WSL portable-runtime results
   as scoped packaging and basic-startup evidence. Public distribution, live
   X11/Win32 input, target permission flow, task effect, and side-effect
   authorization remain separate acceptance checks. The WSL result does not
   establish a live X11 target or native input.

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
