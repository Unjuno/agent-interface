# V39 initial cover-admission rejection evidence rescue A01

This evidence-only rescue carries two original packages from closed PR [#7904](https://github.com/Unjuno/agent-interface/pull/7904) into current main without editing or rerunning their experiment records:

- [Hard invalidation while initial cover admission is pending](v39_invalidated_rejected_submit_recovery_a01_20261005/RESULT.md): the retained baseline sends cancellation after an id-less stale-sequence rejection and waits for a release event that cannot exist. The repair distinguishes rejected/not-admitted from accepted and skips cancellation and planning for the rejected program.
- [Soft-observation stale-submit boundary](v39_soft_observation_submit_rejection_a01_20261005/RESULT.md): a fresh non-invalidating observation advances the sequence; the baseline aborts on the resulting stale-submit rejection, while the candidate records no admission, uses fresh evidence, skips cancellation and the planner turn, and continues from the outer loop.

## H / T / D / C / U

**H.** An initial V39 cover submit can become stale while a newer observation arrives. The controller must distinguish rejected submission from accepted admission before deciding whether to cancel, await release, or start a planner turn.

**T.** The two frozen deterministic FIFO probes cover hard invalidation and a non-invalidating soft observation followed by stale-sequence rejection. Both compare retained pre-repair source with the candidate and preserve their original raw results.

**D.** The original records report 12/12 focused rejection-recovery tests, and for the combined branch 13/13 wait/admission, 6/6 controller, and 13/13 source-refresh tests under normal and optimized Python. These test outputs were not rerun during this rescue. Today, both package manifests verified completely (18/18 and 17/17 files). Both saved read-only auditors passed against the exact archived #7904 source tree. The hard-invalidation auditor run against current main stops at its integrated-source assertion because the helper is not present in main; this is an integration HOLD, not a replacement experiment result. The soft-boundary auditor passed against its frozen source snapshots and retained outputs.

**C.** This is synthetic, source-extracted controller evidence. The current-main audit checks source presence, and the tested current-main renewal composition remains in open Draft [#8018](https://github.com/Unjuno/agent-interface/pull/8018); this rescue does not integrate or approve that runtime change.

**U.** No game, model, GUI, X server, OS input, live threat response, physical key state, application effect, useful feedback, recovery efficacy, latency, or MAP01 outcome is established. Issue #59's live gates remain open.

## Provenance and disposition

The package files are copied from exact PR #7904 head `1403c822609395f9ab21e0cdbb36b7b4c8ee044d`; the original FREEZE, baseline/candidate snapshots, raw outputs, audit scripts, and manifests are unchanged. Only these evidence directories and this index/summary are in the rescue change; no production source or tests are changed. No container or candidate experiment was run.

Keep the old #7904 branch until this rescue is reviewed and the current-main implementation question is resolved through #8018. The old PR and branch history remain the provenance for the original candidate; this page does not promote its construction result to current runtime behavior.
