# MAP01 recovery mechanics development v1

Status: **DEVELOPMENT-ONLY FROZEN; no recovery efficacy claim.**

Base: `b7c6e9935db8e0618e55dd8df2b609b2b036a15f`  
Allocation identity: `map01-recovery-mechanics-dev-01`

## Question

Before consuming the separately frozen formal recovery-vs-coast allocation, can the real ViZDoom/X11 v13 measurement session execute a source-bound bounded recovery interval versus input-free coast while retaining direct release telemetry, scorer isolation and empty terminal release?

## Frozen development pair

Both arms start fresh MAP01 sessions with seed `990615`, skill 1 and a 600 ms planner-wait surrogate.

- **COAST:** one 600 ms coast step; zero input authority.
- **RECOVERY:** one 240 ms `a` hold followed by 360 ms coast. The program is admitted against the current observation sequence, has a 1500 ms absolute lease, and the caller cancels if typed health falls more than 8 points below the source health.

This is not the formal v2 efficacy allocation. The recovery key is a fixed development action, not a new model output. Independent kill/death/exit results are retained but are not used to make an efficacy claim.

## H / T / D / C / U

**H.** The real MAP01 measurement stack can expose bounded recovery input during the wait surrogate while coast admits none, and can verify clean release/scorer isolation without changing the shared runtime.

**T.** Run one fresh coast arm and one fresh recovery arm on GitHub-hosted Ubuntu/Xvfb/ViZDoom 1.3.0. Retain raw runtime/scorer files, terminal score agreement, and the development report. No model calls; no retry selection.

**D.** Development PASS requires coast input admissions = 0; recovery input admissions >= 1; recovery has a strictly lower no-retained-input upper bound under the frozen 600 ms accounting window; all terminal releases are verified empty; scorer missed periods and controller-visible scorer leaks are zero; both arm terminal-score audits pass.

**C.** The session may reject coast composition, release telemetry may not bind the recovery hold, the health guard may expose cancellation, scheduler/capture overhead may distort the nominal window, or terminal scorer agreement may fail. Any first outcome is retained.

**U.** This pair does not isolate useful-control efficacy. Different wall-clock execution and one arbitrary strafe direction can change gameplay. The formal matched v2 question remains gated separately and requires a model-equivalent matched planner condition plus its own lease.

## Promotion rule

A PASS only authorizes implementing the formal matched runner. It does not authorize a Product Hunt efficacy claim. A FAIL identifies the concrete real-MAP01 integration defect to repair before formal allocation.
