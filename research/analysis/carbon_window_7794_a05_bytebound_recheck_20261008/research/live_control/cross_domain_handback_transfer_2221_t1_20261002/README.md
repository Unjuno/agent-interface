# Issue #2221 T1 — retained cross-domain handback source transfer

**Disposition: `PASS_RETAINED_EVIDENCE_TRANSFER_SCOPED`.** This is a bounded
model-free source-transfer candidate, not the live/model recovery test required
by open Issue #2221. It consumes the #1530 retained-evidence HOLD without
changing or relabeling that result.

The four source-bound records distinguish:

1. MAP01 v38 and v39 first exact plan frames: `OBSERVED_CHANGE`, but
   `semantic_task_feedback=unverified` and task effect `UNRESOLVED`.
2. The v39 health revocation's verified physical empty release: a separate
   `PHYSICAL_RELEASE` record, not a task effect or a measured held-key interval.
3. Browser comparison04 direct task-6: an independent exact-once submission
   (`TASK_EFFECT`) even though `AI INTEGRATED SAVED` was not observed and both
   Save/close releases were verified.

The v39 MAP01 run's one kill remains domain progress; map exit is false. The
exact source paths, Git blobs and SHA-256 values are in `SOURCE_HASHES.json`.
Candidate and independent raw-only audit outputs are under `results/t1-01/`.

## Verification and limits

The public six-task archive's existing independent verifier checked all 1,051
members and returned `PASS_PUBLIC_SIX_TASK_CORRECTNESS_SCOPED`, while retaining
`HOLD_INTEGRATION_INCOMPLETE`. New construction tests use the real retained
analysis/audit JSON and reject six evidence-laundering mutations; full tests:
see the frozen run/audit records.

No model, game, GUI, OS input, network task call, or shared allocation was
used. Docker Desktop's Windows service was stopped, so no container ran and no
service was started. No cross-source latency, same-clock relation, useful DOOM
feedback, recovery decision, task-value improvement, held-out transfer, human
tempo, or product result is claimed. Live routes with independent scorers and
model recovery remain outstanding under #2221; the Issue is not closed by this
pre-model result.
