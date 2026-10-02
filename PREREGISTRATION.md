# #5694 A03 — first-failed-boundary attribution controls

## H / T / D / C / U

**H.** With exogenous opportunity times fixed, moving cue phase across an unchanged capture schedule changes only the earliest missed boundary to `not_acquired`; holding capture/delivery fixed and injecting a planner stall changes the classification to `delivered_no_decision`. The complete ledger will separate these cases and preserve `UNKNOWN`, safe stop, and no-clock cases without synthesizing missed actions.

**T.** One deterministic, standard-library-only event replay with eight exogenous opportunity rows plus a no-clock `NOT_APPLICABLE` control (nine ledger rows total). Include: phase-hit and phase-miss controls; a cue captured but delivered after expiry; a delivered cue with no decision before expiry; a decision with no independently verified effect; a safe-stop control; unsynchronized-clock and right-censored UNKNOWN controls; and a no-exogenous-opportunity `NOT_APPLICABLE` control. The fixture exposes controller-visible capture, delivery, decision, and typed effect-receipt events separately from scoring-only truth. The candidate receives only the frozen event fixture and emits one boundary classification per declared opportunity. An independent raw-only auditor, not importing candidate code, reconstructs every row and validates any effect receipt against the scoring-only oracle.

**D.** `PASS_METHOD_SCOPED` only if all nine ledger rows (eight unique exogenous opportunity keys and one `NOT_APPLICABLE` control) are retained exactly once, the phase and planner-stall contrasts land at their preregistered different boundaries, safe-stop/clock-unknown/censored/no-clock are not mislabeled as misses, the independent auditor agrees on all rows, and all five frozen raw corruptions are rejected. Otherwise preserve `FAIL_METHOD` or `STOP` according to whether the failure is semantic or execution/provenance related. No live-effect inference follows.

**C.** This fixture may be too easy because event identities are explicit; an operational system may not expose reliable capture/delivery/decision joins. A single independent outcome receipt may already be sufficient without first-boundary attribution.

**U.** Authored deterministic schedule only. No model, GUI, input, real clock sleep, game, route comparison, safety-rate estimate, or #59/live-control evidence. Boundary counts do not establish causal prevalence.

## Frozen execution

- Allocation: `EXOGENOUS-OPPORTUNITY-BOUNDARY-5694-A03-20261002-01`
- Owner: this Codex desktop research task; native Windows CPU only, no shared WSLc/container/GPU resource.
- Intake main at initial selection: `adfb333264ed323a142170778f121a00b3970448`.
- Pre-freeze refresh: `a11b1d811aea94d65a7c7a66073f1c9a7d024624`; the seven intervening commits touch `research/analysis/README.md`, #5911 route-selector evidence, and #6669 control-plane evidence only. Direct comparison found no overlap with this additive #5694 package. All candidate/fixture/test bytes remain unchanged.
- Branch: `research/exogenous-opportunity-5694-first-failed-boundary-a03-20261002`.
- Evidence path: `research/analysis/exogenous_opportunity_5694_first_failed_boundary_a03_20261002/`.
- Planned one-shot local window: 2026-10-02 19:40–19:55 UTC. Candidate max 1, independent auditor max 1, retries 0.
- Runtime: Windows CPython 3.11.9, standard library only. No WSLc invocation, Docker/OrbStack, network, model, GPU/CUDA, GUI, or user data.
- Candidate, independent auditor, fixture, and construction tests are frozen before the formal candidate/auditor pair. Output paths must be absent before the single candidate invocation. If a precondition fails, record STOP and do not retry.
- Formal local outputs: `execution/formal-01/candidate.raw.json` and `execution/formal-01/audit.json`; both must be absent at the pre-run collision gate.

## Pre-formal construction chronology

The first construction suite invocation passed 7/8 checks and exposed a candidate/auditor receipt-detail label mismatch. No formal candidate, auditor, container, model, or GUI invocation occurred. The labels were aligned before freeze. A subsequent semantic review also found that a right-censored trace with a capture/delivery but an unexpired opportunity must remain `UNKNOWN`; both implementations now apply that censoring rule unless a terminal safe stop or verified effect is already observed. These are pre-formal construction corrections, not experimental outcomes. The final construction suite passes 8/8.

This is a distinct supplemental discriminator under existing #5694, not a rerun or regrade of A01/A02 or their records.
