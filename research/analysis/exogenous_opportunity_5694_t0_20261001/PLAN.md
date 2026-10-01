# Issue #5694 T0 — exogenous opportunity denominator

Allocation: `EXOGENOUS-OPPORTUNITY-5694-T0-20261001-01`  
Additive path: `research/analysis/exogenous_opportunity_5694_t0_20261001/`  
Docker status: Docker Desktop CLI is installed, context is `desktop-linux`, but `com.docker.service` is Stopped/Manual and no Desktop/backend process is running. No Engine/container inventory is available. This finite standard-library experiment will run once on the host CPU; no service start, image pull, or container change.

## H / T / D / C / U

**H.** A closed-loop completed-cycle latency statistic can remain unchanged while an independently defined exogenous opportunity stream experiences missed or late useful effects during declared busy periods; retaining every opportunity detects the false “no degradation” interpretation. With no stall, the ledger must show no false loss. Unsynchronized clocks must yield UNKNOWN rather than manufactured latency or opportunities.

**T.** Freeze six deterministic finite cases: (1) ten opportunities, no stall, service 2 ticks, deadline 4; (2) the same schedule with controller busy on [25,65), producing silent omitted attempts but the same 2-tick completed-cycle latency; (3) the same busy interval with explicit safe-stop outcomes; (4) service 5 against deadline 4; (5) four overlapping opportunities at ticks 0–3 with one serial service lane; (6) three opportunities with unknown clock alignment. Emit one hash-bound JSONL row per preregistered opportunity, including missed/late/safe-stop/unknown rows. A separate raw-only standard-library auditor independently reconstructs every row, denominator, latency, deadline outcome, coverage, and four corruption controls. Construction tests are not formal rows. Candidate and auditor each run once after remote source freeze; no retry.

**D.** `PASS_METHOD_SCOPED` only if all declared opportunities remain represented exactly once; the busy case has the same p95 of completed cycles as baseline while lower useful-opportunity coverage; the no-stall control remains full coverage; safe-stop is distinguished from useful completion; expiry and overlap are classified correctly; unsynchronized timing remains UNKNOWN; the independent audit has zero errors and rejects all four controls. `FAIL_METHOD` for denominator loss, a missed opportunity presented as completed/absent, wrong deadline/queue result, or fabricated synchronized duration. Integrity/source mismatch is STOP. Any PASS is only finite measurement-method construction, not evidence about a live agent.

**C.** Six hand-authored deterministic cases; integer abstract ticks; standard library only; one candidate and one independent audit. The external opportunity stream and expiry are fixed before controller outcomes. The baseline, busy-silent and safe-stop arms share identical opportunities. Completed-cycle p95 uses nearest-rank over dispatches that returned; opportunity coverage independently uses all declared events.

**U.** No live planner stall, model, GUI/game, user input, OS action, actual first useful feedback, production clock, causality, safety, task success, human-tempo, or performance claim. Clock uncertainty cannot be resolved by this simulator. No coordinated-omission histogram correction is applied. The result cannot justify synthetic action opportunities for tasks that lack an external schedule.
