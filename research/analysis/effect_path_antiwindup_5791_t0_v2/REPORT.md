# Issue #5791 T0-v2 result — 2026-10-01

**Disposition: `PASS_METHOD_SCOPED`; `FAIL_INCREMENTAL_VALUE_VS_SIMPLE_CAP` for the preregistered H in this synthetic family.** The planted integrator mechanism was detected and the independent raw-event oracle passed, but receipt-aware anti-windup did not improve on a one-outstanding-action cap held until semantic-effect receipt. This is not a live/runtime result.

## H / T / D / C / U

- **H:** Not supported in this fixture: C had no incremental benefit over the stronger semantic-receipt queue-cap B.
- **T:** One deterministic candidate run and one independent audit across 5 cases × 3 policies = 15 rows. No GUI, model, external service, or user data.
- **D:** Method/oracle gate passed: all 15 rows independently reconstructed with zero mismatch; the negative no-integrator control was invariant; ambiguous delivery retained an UNKNOWN interval; old-generation queued commands were canceled before effect; mandatory cancel latency remained zero. The H value gate failed because B matched C on overshoot, final error and safety outcomes in the eligible cases, while B completed the known saturation case one tick earlier.
- **C:** A simple one-slot queue held until a source-bound semantic-effect observation appears sufficient for these cases. Generation cancellation separately blocks stale intent. Extra anti-windup state/tracking is not justified by this trace family.
- **U:** All schedules, targets, effects and labels are synthetic and deterministic. The fixture was authored to expose a mechanism; counts are not rates. No LLM-as-PID equivalence, real Agent Interface windup, deployment frequency, causal effect, human tempo, live safety, or product claim.

## Frozen environment and evidence

Allocation `effect-path-antiwindup-5791-t0-docker-20261001-02`, based on main `889cbada566553610c58fa1f92b5b6fa1a3563ff`. Docker Desktop 29.8.0 linux/amd64; `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, network none, 1 CPU, 256 MiB, pids 64. Candidate and auditor each exited 0; raw 6,047 bytes. Raw/candidate SHA-256 `3DC5DDEF109B4016D3ACE4EB6DDD0FEEA7D5E390732C4D573D54139F8E8CFB14`; audit stdout SHA-256 `991F364FFAC4508710A1CACBACF34D88F67EF968741C7DA2FD78B7EC0DA0D28E`.

## Results

| Case | Unrestricted accumulation A | Semantic-receipt cap B | Receipt-aware anti-windup C |
|---|---|---|---|
| Integrator saturation/release | 4 queued corrections; overshoot 3 | overshoot 0; effect at tick 4 | overshoot 0; effect at tick 5 |
| Transport ACK before effect | 2 effects; 1 duplicate; overshoot 1; UNKNOWN recorded | 1 effect; no duplicate; UNKNOWN until observation | same as B |
| No integrator state | same outputs | same outputs | same outputs |
| Goal changes while blocked | 3 old-generation commands canceled; 0 stale effects | 1 canceled; 0 stale effects | 0 old commands; 0 stale effects |
| Mandatory cancel | 0-tick bypass | 0-tick bypass | 0-tick bypass |

Thus receipt awareness beats unrestricted retry/accumulation on the ambiguous-delivery case, but the stronger queue-cap baseline does the same. The experiment does not support adding C beyond B. It also shows why transport ACK cannot be treated as semantic effect confirmation.

## First allocation retained

Allocation 01 remains at `../effect_path_antiwindup_5791_t0_v1/` as `FAIL_CONSTRUCTION_METRIC_CONTRACT_MISMATCH`: its candidate exited 0 and independent auditor exited 1 after counting feedback-separated effects as duplicates and conflating stale-generation cancellation counts. No rerun or relabeling was made; v2 is separately frozen.

No live T1 was attempted: this T0 does not establish that any current #59/#57 path contains an explicit accumulated correction state. The Issue remains open for source-bound eligibility evidence or a genuinely different successor hypothesis.
