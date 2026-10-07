# Issue #8068 T1 — retained-trace eligibility audit

## H / T / D / C / U

**H.** At least one retained repeated-recovery trace will expose a stable fault class, typed recovery-operation scope, exposure denominator, independent post-recovery health/effect oracle, recurrence/censoring, and worker-age/load covariates, making repair-history analysis identifiable.

**T.** Read-only, bounded audit of four nearest retained records on current main `978c3782e62cd509e0d304abecb8e27f0ef3f6b8`: the exact-scope recovery record from #7042, worker lifetime/rejuvenation study #6133 T1c, recovery-rate study #5776 T0-v2, and closed MAP01 repeated no-progress repair study #557 V2. Review used each record's issue/PR summary and retained report/README where linked. No source, historical outcome, raw trace, process, container, GUI, or input was modified or rerun. Scope is this targeted candidate set, not a repository-wide absence proof.

**D.** `HOLD_NO_IDENTIFIABLE_REPAIR_HISTORY`. None of the four records is an eligible observed repeated-recovery cohort with all required fields. #7042 establishes tracked-input neutralization only, explicitly not process/session reset or fault cure. #6133 T1c's 600 records and typed restart policies are authored synthetic worker-aging traces; its own U says no real process aging/restart and no qualified actual-worker rejuvenation path. #5776 T0-v2 is a 336-episode/40,320-event synthetic disturbance/recovery fixture, not observed typed repair operations or task-effect recovery. #557 V2 has genuine repeated no-progress navigation corrections and independent exploration/release scoring, but those corrections are not reset/rejuvenation operations; it has no worker-age/load covariates or per-recovery independent task-effect cure oracle. No candidate supports the stipulated repair-history estimand.

| Record | Fault / operation | Exposure and recurrence | Independent post-recovery truth | Age/load | T1 disposition |
|---|---|---|---|---|---|
| #7042, X11 input recovery | One operation class: release tracked inputs; explicitly not process/session reset or cure | No repeated fault recurrence cohort or denominator | Input readback only; task success stays unknown and replay is disallowed | Not relevant/absent | Exclude: input neutralization, not fault repair |
| #6133 T1c, worker-aging | Typed restart policies in authored simulator | 5×3×40 synthetic job records; modeled cycles only | Simulated obligations/generation receipts, not actual worker or application health/effects | Authored worker-age/RSS/latency/thermal covariates | Exclude from empirical T1: synthetic method fixture; actual path remains unqualified |
| #5776 T0-v2, recovery sentinel | Disturbance mechanisms, not typed recovery intervention history | 336 authored episodes / 40,320 event rows; return intervals modeled | Event replay oracle validates simulator arithmetic, not task/effect restoration | Load strata are authored; not worker age/load observations | Exclude: no observed repair-operation cohort |
| #557 V2, MAP01 no-progress deopt | Repeated small/large navigation corrections, not restart/reset | Four matched MAP01 seed pairs; no per-repair fault-cure recurrence denominator in retained summary | Evaluator-only trajectory coverage and InputOwner release audit; no per-repair effect-cure oracle | None reported | Exclude: adjacent navigation adaptation, not typed recovery history |

**C.** The #557 study is the closest retained real-environment analogue because it observes repeated repair actions and independently scores trajectory. The other closest records either establish a safe but non-curative input-release operation (#7042), or contain rich but authored lifecycle/recovery histories (#6133, #5776). These distinctions prevent treating “a later task worked,” a restart receipt, a queue return, or a navigation correction as proof of repair.

**U.** This is a targeted eligibility result, not proof that no suitable trace exists anywhere in the repository or in unindexed/private host records. No recurrence probabilities, causal repair effects, calibration, or policy value are inferred. The HOLD is not a software-aging/sentinel FAIL and does not authorize any retry, reset, or live allocation.

## Evidence refs and next gate

- Baseline: main `978c3782e62cd509e0d304abecb8e27f0ef3f6b8`, 2026-10-05. The selected evidence files were read at `b422026a83d0cdebbf5aa80df63fa883db4511ab`; a subsequent compare found none of these evidence paths changed on the advance to `978c3782e62cd509e0d304abecb8e27f0ef3f6b8`. The research branch was rebased before publishing.
- #7042: `research/analysis/issue_7042_x11_input_recovery_scope_t0_20261004/REPORT.md`; disposition `INPUT_NEUTRALIZATION_ONLY`.
- #6133: `research/analysis/worker_aging_6133_t1c_20261002/REPORT.md`; 600 authored records, `PASS_METHOD_SCOPED`, but empirical aging cohort explicitly remains held.
- #5776: `research/analysis/recovery_sentinel_5776_t0_v2/REPORT.md`; 336 authored episodes, method failure on the frozen sentinel, no deployment data.
- #557: issue comment [5700538032](https://github.com/Unjuno/agent-interface/issues/557#issuecomment-5700538032); V2 `PASS_BOUNDED_DEOPT_COVERAGE / PASS_AUDIT`, bounded to `-nomonsters` navigation.

Next useful evidence is a separately captured, complete repeated-recovery trace from a disposable resettable fixture or owned worker, with typed intervention identity/scope, opportunity-level exposure, independent health/effect receipts, recurrence and censoring, and age/load controls. Any such prospective run needs a new predeclared freeze and its own authorized allocation; this HOLD does not inherit or authorize one.
