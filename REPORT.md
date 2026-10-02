# #5694 A03 — first-failed-boundary attribution controls

**Raw audit:** `PASS_METHOD_SCOPED` (9/9 rows replayed, zero errors, 5/5 corruption controls rejected).  
**Post-run hypothesis adjudication:** `HOLD_PHASE_CONTRAST_NOT_MATCHED`; the phase pair did not hold capture schedule and observation horizon constant as required by H.

## H / T / D / C / U

- **H:** A phase-shifted cue missed by an unchanged capture schedule should localize to `not_acquired`, while a planner stall after fixed capture and delivery should localize to `delivered_no_decision`.
- **T:** One deterministic Windows CPython 3.11.9 standard-library run, with nine exogenous opportunity rows plus one no-clock `NOT_APPLICABLE` ledger row. No model, GUI, input, real clock sleep, network, WSLc, Docker/OrbStack, GPU or CUDA.
- **D:** Candidate exit 0; independent raw-only auditor exit 0; all nine rows independently replayed; all five frozen corruptions rejected. The classification mechanics pass their scoped replay gate. A post-run H audit found the phase pair changed both capture schedule and horizon, so the phase result is not a matched test of H; overall hypothesis disposition is HOLD, not PASS.
- **C:** Authored event identities and synthetic oracle may make the boundary joins easier than in an operational trace. Capture-phase effects could not be separated from the changed schedule in this fixture.
- **U:** Synthetic finite method fixture only. No evidence about live coordinated omission, actual capture/planner systems, safety, #59/DOOM control, human operating tempo, or product benefit.

## Frozen run and raw outcomes

Allocation `EXOGENOUS-OPPORTUNITY-BOUNDARY-5694-A03-20261002-01`, based on main `a11b1d811aea94d65a7c7a66073f1c9a7d024624`. Candidate and independent auditor were each invoked once, both exited 0, retries 0. The run took place on native Windows CPU from 19:40:39.1226745Z to 19:40:39.4021400Z. No container/runtime or GPU was touched.

| Case | Frozen ledger classification |
|---|---|
| phase_hit | eligible_effect |
| phase_miss | not_acquired |
| delivery_after_expiry | acquired_not_delivered |
| planner_stall | delivered_no_decision |
| decision_no_effect | decision_no_eligible_effect / no_verified_effect |
| safe_stop | decision_no_eligible_effect / safe_stop |
| clock_unknown | UNKNOWN / clock_unsynced |
| right_censored | UNKNOWN / right_censored |
| no_exogenous_opportunity | NOT_APPLICABLE |

Candidate raw SHA-256: `c76474a97505411cfd88b8808c2caa616017c6952bdba75614c941d629f03f39`. Auditor JSON SHA-256: `6a43bd87297aef6c08eb394a26b86362253aa753de4017135d2279366e8771de`. Exact commands, exit captures, source/input hashes and all stdout/stderr are retained in `FREEZE.json`, `RUN_RECORD.json`, and `SHA256SUMS`.

The audit PASS proves only replay of these authored rows and corruption controls. It does not overcome the unmatched phase fixture; see `ADJUDICATION.md`. Previous #5694 A01/A02 results remain untouched and unpooled.
