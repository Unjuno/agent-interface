# Computer control investigation plan — 2026-11-13

## Purpose

Move the computer-control goal forward by closing the currently visible gap between a recovered/released input and a verified MAP01 task outcome. Keep each uncertainty classified separately: caller evidence integrity, deadline/expiry, OS input state, application queue/task effect, and terminal task oracle. Do not promote a neutral input horizon to proof that queued application work is absent.

## Verified starting facts

- The active thread goal still exists and is active. A second goal cannot be created while that goal is unfinished; continue it rather than replacing it.
- Main worktree for this task is clean at `195fc6cdd2b1f30396fd5c846225c7fb04c172b4`.
- R156 is a composed-path FAIL/UNKNOWN. Its independent sampler observed W down 8.0001 ms after the lease expiry and first fully-post-expiry up at 9.2503 ms; a later state read showed release, but the public receipt lacked release confirmation and the task oracle was not reached.
- R156's runner then failed on missing `expiry-held-w-samples.json` while the server reported a pending-call resolution error. The target was kept open for one state read, but not for the required continuous two-second post-run horizon. The click/task effect therefore remains unknown.
- A separate, exact-source orphan recovery later released W and left mouse on a fresh target generation, verified neutral readback and a two-second horizon (77 observations, max gap 30.018 ms), kept the original action UNKNOWN and replay denied, and cleared durable custody (revision 428). This is recovery evidence, not R156 task-success evidence.
- R157 preregisters the focused correction: keep expiry samples separate from pending resolver records, use exact call-id reconciliation, observe a bounded independent two-second same-generation neutral horizon on normal and exception paths, and require every existing task/effect gate before close.
- The R157 packet is not yet frozen or run. Its freeze script contains a tautological runtime-tree comparison, which provides no assurance; remove that check and retain only the comparison against the frozen authoritative commit.

## Investigation questions

1. Does R157's exception path preserve a valid public result for the exact dispatched call without confusing expiry sampler data with resolver output?
2. Can the independent neutral observer prove continuous same-process, same-generation release within its bounded sample-gap and read-bracket limits?
3. Does the public action receipt confirm release independently of the sampler, and does the same-run ammo oracle plus demo audit distinguish task effect from later queued/application effects?
4. Are any terminal failures caused by the integrated runtime/caller, the evidence join, the observation boundary, target/environment, or the task oracle?
5. Only after correctness gates pass: what remains to produce a comparable #57 efficiency estimate with all failed attempts retained?

## Finite execution plan

1. **Prepare and freeze:** repair the R157 freeze-script tautology; compile runner/helpers; run the focused repository tests for evidence joining and neutral-horizon sampling, plus the packet's adjudication/contract tests. Freeze source, runtime/research hashes, package identity and clear custody state. Verify the freeze before launching a target.
2. **One fresh integrated run:** execute the preregistered single-dispatch R157 public compiled-supervised MAP01 attempt. Preserve every raw file and initial failure. No retry or replay. Keep the target open through the independent horizon and exact-call reconciliation; close only after all predeclared release and task gates pass.
3. **Classify before changing code:** adjudicate runtime release, expiry bracket, held-input evidence, horizon, numeric ammo transition, task-oracle receipt and scoped demo trace separately. If a gate fails, stop that attempt and repair only the demonstrated seam in a new frozen source/attempt.
4. **Record and integrate:** write an additive result report with source and raw hashes, exact conditions, outcome, limitations, and the next decision. Promote only a demonstrated fix with local tests. Keep unrelated Docker settings, runtime-download UX and Calc economics out of this MAP01 experiment.
5. **Then resume #57:** design matched same-model comparisons with all attempts, actual token/model usage, end-to-end latency, correctness and release gates. Existing small or instrumented observations do not establish a speedup.

## Stop and acceptance rules

- At most one dispatch in R157. Never replay an uncertain action.
- Missing/stale identity, generation, exact-call receipt, release evidence, neutral horizon or task oracle means FAIL/UNKNOWN for the corresponding claim.
- Release success does not imply task success; a two-second neutral input horizon does not establish application-queue quiescence.
- A task-effect pass requires independent same-run numeric change 50→49, exact final dispatch/call linkage, valid public task-oracle receipt, and the preregistered demo audit.
- No speed claim from this single instrumented run. Report local checks separately from live evidence and any optional CI.

## Current next action

Run the focused checks and repair the preflight script's tautological comparison. If frozen verification succeeds and custody remains clear with no GZDoom process, proceed with exactly one R157 run under its preregistration.

