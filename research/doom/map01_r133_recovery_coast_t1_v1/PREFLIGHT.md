# MAP01 r133 recovery-vs-coast T1 — local preflight

Status: `HOLD_PREREGISTRATION_INCOMPLETE`. This note records current-main feasibility checks only. It is not the formal preregistration, a live/game result, or permission to start a container.

## Identity and scope

- GitHub repository: `Unjuno/agent-interface`
- Local source base: `33c19225f117d6d927a98e791e620de37479a927` (main at preflight)
- Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59)
- Queue request: #5085 comment [#5921114962](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5921114962), allocation `MAP01-R133-RECOVERY-COAST-59-T1-DESKTOP-20261002-01`
- Proposed CPU-only Docker Desktop window: 2026-10-02 00:00–01:00 UTC. The comment is a request only; no lease or container permission was observed.

The local component checks below ran against `33c19225f117d6d927a98e791e620de37479a927`. A final GitHub recheck found `main` had advanced to `7c98ac44c432ad1b2e3b9834e54bdeda734e4bfa` via an additive Issue #4373 evidence commit. Its changed paths are confined to `research/verification/submit_purpose_s6p1_v1/**`; none of the checked MAP01/owner/scorer sources changed. The local branch was rebased onto that current main, so its current base is `7c98ac44c432ad1b2e3b9834e54bdeda734e4bfa`. Re-freeze all source identities again at formal start.

## H / T / D / C / U (provisional)

- **H:** A bounded, explicitly guarded recovery cover during model inference produces more independently scored useful MAP01 progress and less unsafe unprotected time than unauthored coast under matched threat-contact conditions.
- **T:** The request proposes three counterbalanced matched pairs (six restored sessions), recording source intent, observations, actual input occupancy, guard invalidation, health/ammo/progress, first independently scored useful effect, and terminal release. No new candidate implementation has yet been frozen.
- **D:** Not frozen. The request's qualitative comparison is insufficient by itself: specify the independently scored event inventory, plan/actuation binding, exposure denominator, pair-level summaries, and PASS/HOLD/STOP rule before any candidate call. Lack of a useful event must not be counted as a pass.
- **C:** Exact fixture/save, controller/policy, model contract, image digest/platform, engine context, and per-arm task exposure remain to be frozen at the actual start gate.
- **U:** At most a small matched-fixture result; no MAP01 clear, population reliability, human-tempo, or cross-domain claim.

## Existing evidence that must not be repeated or promoted

- Closed Issue #428 remains `FAIL_INTEGRITY_ANALYZER_COVERAGE`; its v39 partial-admission counterexample is preserved.
- Its additive successor, closed Issue #443, already reconstructs and independently audits the complete v38/v39 logs. Its immutable result is `SCHEMA_CENSORING_TOO_WIDE`: v39 interval-width/upper is `0.25453708285828974` against the frozen `0.25` gate. Do not rerun or tune this posthoc.
- The retained first-useful-feedback audit (#503) establishes some independently reconstructed HUD state changes, but no plan-bound independently scored task-effect timestamp in the retained v38/v39 traces.
- The #1907 R0 bridge is a scoped synthetic lineage PASS only. It does not establish that the current MAP01 runtime emits joined physical-edge evidence.
- Issue #5156 is the designated explicit KeyRelease/XSync measurement successor. Its proposed A09 slot on #5085 is still request-only in the latest queue read; terminal STOP/cancellation is not equivalent to a passed release-measurement prerequisite.

## Current-source feasibility findings

1. The current-main GitHub copy of `research/doom/session_map01_v6.py` (directly fetched at the recheck) emits `post_control_score` only on `finish`, so it does not timestamp a first useful kill/exit during a plan. The sparse local checkout does not include this file; it was not locally executed or hashed in this preflight. The v23 effect receipts classify viewport pixel change and expressly do not call it useful feedback.
2. The retained `input_owner_v10.py` timestamps admission and eventual empty release, but not each normal per-key `up`. `input_transition_owner_v3.py` brackets the caller-side RPC around a fake/inner owner in its tests; it does not prove an owner-thread KeyRelease-to-XSync bracket. Do not label that bracket as exact physical occupancy.
3. Existing scorer components offer a possible authority-separated path: `independent_progress_clock_v2.py`, `main_thread_scorer_polling_v1.py`, and `map01_scorer_stdio_adapter_v1.py` can retain scorer-only kill/death/exit samples outside the controller-visible stream. They are not yet integrated into the proposed v23 session or bound to a physical actuation/plan.

## Local construction checks

Run against the sparse local checkout of the exact base above; these checks do not use Docker, X11, the game, a model, or input:

| Check | Result | Boundary |
|---|---:|---|
| Existing input-transition wrapper tests, Windows CPython 3.12.10 | 8/8 PASS | Fake inner owner only; caller bracket, not owner-thread release timing |
| Existing independent progress clock tests, Windows CPython 3.12.10 | 15/15 PASS | Deterministic scorer contract only |
| Existing scorer polling tests, WSL Ubuntu | 12/12 PASS | Fake I/O/pipe construction only |
| Existing scorer file-adapter tests, WSL Ubuntu | 5/5 PASS | Retention/schema construction only |
| Same polling/adapter tests, Windows | 1 failure in each file | Platform limitation: Python `select()` cannot watch these Windows pipes (`WinError 10093`); WSL reruns passed. Preserve this host-specific failure; do not count the native-Windows invocation as green. |

These are existing component suites, not a new hypothesis result. No Docker command, image inspection, game process, model call, candidate, auditor, seed, or formal allocation was run.

## Required gates before a formal candidate

1. Refresh main, open/closed issues, branches, PRs, #5085 queue, and current owner claims. Require an exact lease; recheck #5156's A09 terminal disposition and whether its measured owner-thread release bracket actually passed. If it stopped or did not provide the required identity-bound timing, keep T1 on HOLD or freeze a separately audited implementation first.
2. Freeze a new additive MAP01 controller/session version only if needed; do not silently substitute v39 or call the older v23 path current-main behavior. Add a plan/step/actuation lineage check, real per-key owner release brackets, and scorer-only event sampling/binding. Test mutation rejection and prove scorer data never reaches the controller.
3. Define the independent useful-event taxonomy and exact pairing/statistic/decision thresholds. Distinguish state feedback, useful effect, safety outcomes, and model wait; do not infer causal credit from time overlap alone.
4. Freeze all source, fixture/save, prompt/model, cached image digest/platform, and isolated `desktop-linux` context/inventory. If any prerequisite or slot is absent, record a pre-run STOP/HOLD without invoking Docker.
5. Only after these gates, run one candidate orchestration and (only on candidate exit 0) one separate raw-only audit. No retries, image pulls/builds, GPU, or identity reuse.

This preflight deliberately leaves the queue request and all historical results unchanged. It does not authorize execution.
