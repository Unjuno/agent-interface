# #5855 horizon-ledger transfer audit A02

## H / T / D / C / U

- **H:** Applying task-ID accounting and an explicit finite observation horizon to the retained six-cell #5855 route-addition T0 will conserve every offered task across baseline, greedy, capped, central, and held-out disjoint-control arms. A fixed horizon will classify some late tasks as right-censored rather than allowing their post-horizon eventual completion to leak into observed throughput.
- **T:** Read, but do not alter or rerun, the immutable raw candidate result from `braess_route_verifier_5855_t0_v1` at main `bb3138d019118bf050fe1136a9ba3619146bb46e`. For each cell, set one common horizon to `last_offer_time + 32` ticks (the predecessor's frozen deadline). Emit one OFFER per task and exactly one VERIFIED_TERMINAL (completion at/before horizon) or RIGHT_CENSORED (completion after horizon) classification. Include baseline, greedy, capped, and central arms in all six cells, plus baseline/greedy disjoint controls in the held-out cell. Candidate runs once; a separately implemented auditor reconstructs all 416 task rows and the event-prefix conservation invariant from source raw data.
- **D:** `PASS_HORIZON_LEDGER_TRANSFER_SCOPED` only if the source hash and source commit match the freeze; all six cells and 26 arms reconstruct exactly; every task ID has one offer and exactly one observed terminal-or-censored classification; no duplicate receipt or disappearance is accepted; at every event prefix `offers = verified terminals + right-censored + active`; all terminal rows retain exact-effect, safety, and release flags; the held-out baseline/greedy difference is stated without substituting complete-only latency for the denominator-complete result. Otherwise `FAIL_ACCOUNTING`/`HOLD` with the failed gate retained.
- **C:** This is a deterministic accounting projection of the predecessor's synthetic schedule. It changes neither route choice nor any source outcome and does not independently revalidate the predecessor's discrete-event simulator. The common horizon is an explicit A02 analysis boundary, not the original T0 deadline gate.
- **U:** No live runtime, task generation, model, GUI, input, or production queue is tested. Source traces contain precomputed eventual completions; the exercise tests horizon classification and accounting, not online censor detection or stationarity. The result cannot establish an operational Braess effect.

## Frozen constants and source

- `N=16`, `deadline_ticks=32`, cell intervals `{16, 8, 2}`, fast verifier work `{8, 12}`.
- `horizon = 15 * arrival_interval + 32` for every arm within a cell.
- Task identity is the predecessor's integer task ID; one task is one offer regardless of route.
- Terminal receipt ID is `scenario/arm/task_id/VERIFIED_TERMINAL`; censor receipt ID is `scenario/arm/task_id/RIGHT_CENSORED`.
- Frozen predecessor raw SHA-256: `ba5ee3c03bcf1105fd6bbbd0278b710fffb014cdd865f988f2d5649cb0bb4361`.
- Frozen predecessor manifest SHA-256: `c2435408c1e7117a909fb95d9151bfaadfa231db30d9a3d83d6d6f5ba3b73828`.

## Execution boundary

The retained source is consumed read-only. No model or external service is called. This deterministic CPU-only transform is suitable for isolation, but the host's OrbStack Docker daemon currently responds to metadata/image enumeration with a missing containerd content blob (`operation not supported`). No container is started; any execution below uses the frozen host interpreter and is reported as a runtime limitation, not container validation. Do not repair/reset the daemon or retry the experiment under a changed runtime in this allocation.
