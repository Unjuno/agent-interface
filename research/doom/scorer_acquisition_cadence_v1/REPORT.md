# Scorer acquisition closure and cadence experiment

Decision: **PASS the versioned acquisition fix; HOLD the 5 Hz optimization.**
Issue #137; successor to #121 / PR #134. Publication base `6378447b4b6756aae0abb00733b9eb4c3d24630f`; executed runtime base `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`. Only new research files are added. No historical runtime, workflow or retained allocation is modified. No model calls.

## 1. Close the actual outstanding defect

Current-main `ScorerFileSink.direct(sample_game(), clock)` evaluates its sample before obtaining both bracket endpoints. Replaying the 33 inherited final records confirms **0/33 valid final acquisition brackets**, even though final score values agree. Their source archive SHA-256 remains `09415497dba0d8c0635ff9b0ea10ebec15c703640d4eadbdf1c257e6bdf3b67c`.

The new `FinalAcquirer` brackets the callable, not a pre-evaluated value. It acquires once, checks integer clock ordering and payload containment, and only then persists. A failed final attempt cannot be silently retried on that object. The versioned session uses this route at close, validates periodic receipts too, and closes the engine even if final acquisition raises. All game access remains on its owning main thread. This is an acquisition-order contract, NOT a source-freshness or exact effect-time proof.

The first setup preflight failed on missing Pillow in the new virtual environment, before game/input. Fixed local wheel dependencies were installed without changing the measured code. A separately identified 250 ms, one-key preflight then passed. Both are excluded from the comparison and retained.

## 2. Freeze and run one-variable cadence comparison

Freeze commit: `63f42b01afce714ca981c41a61cc1d7ccb58a625`.
Full plan SHA-256: `1c30e5822d1acddebb3f397771a4a13112b2f4a70f8ed75ce4418890fa4d4b39`.

18 fresh real MAP01 sessions: three modes x six restores. The six possible order permutations are used once each. All modes have the SAME acquisition repair, keys `[s,a,space]`, requested hold 5000 ms, owner-authority cutoff 3075 ms, fixture, renderer, input path and nominal 20 Hz clock-command load. Only evaluator refresh/cadence changes. Existing X11/Executor/InputOwner semantics are retained; expected terminal is `expired`, not `completed`.

| Condition | Value |
|---|---|
| CPU / affinity | AMD EPYC 9V74 / CPUs 0-4 |
| Frequency | Unpinned, shared host; no calibrated fixed frequency |
| Python / kernel | CPython 3.13.5 / Linux 6.18.44 |
| Engine | ViZDoom 1.3.0, Freedoom MAP01, skill 1, ASYNC_SPECTATOR, 35 tics/s |
| Input/rendering | Real XTEST; private Xvfb/Openbox 1280x800; game 640x480 |
| Libraries | Pillow 12.3.0, NumPy 2.5.3, python-xlib 0.33, openpyxl 3.1.5 |
| Restore state | threat-contact-v2; saved RNG, not independently sampled maps |
| Policy / planner | Fixed development keys; zero model calls; no scorer feedback to policy |
| Runtime bundle | artifact 10398313098; 2592 source and 12 wheel hashes verified |

`advance_action(1, True)` is an explicit evaluator intervention, not a non-perturbing passive observer. Official method semantics distinguish state update from merely obtaining the stored state: https://vizdoom.farama.org/api/python/doom_game/ . The measured conclusion is scoped to installed 1.3.0 and this runtime, not inferred solely from current documentation.

## 3. Results

| Mode | Final kills | Positive observed before cutoff | Source tics per case before cutoff | Refresh calls before cutoff, per case | Total refresh blocking per case, median [range] |
|---|---:|---:|---:|---:|---:|
| Passive getters 10 Hz | 6/6 | 0/6 | 1 | 0 | 0 ms; stale evidence |
| One-tic refresh 10 Hz | 6/6 | 6/6 | 31 | 31 | 523.027 [434.391, 693.784] ms |
| One-tic refresh 5 Hz | 6/6 | 6/6 | 16 | 16 | 379.144 [208.540, 555.197] ms |

All 18 final scores are one kill, zero deaths, no exit, alive and unfinished. Health remains 97 to 97; ammo 48 to 40. These controls do not establish survival or navigation benefit. The observation-time difference is not a faster-kill result.

Refresh blocking counts only calls whose resulting sample timestamp is at/before the owner deadline. It includes the initial periodic acquisition before admission, and excludes final-after-control acquisition. It is wall blocking time, not CPU time, end-to-end task duration, or exact engine-event latency.

| Block | 5 Hz / 10 Hz blocking ratio |
|---|---:|
| 1 | 0.421432 |
| 2 | 0.738711 |
| 3 | 0.426477 |
| 4 | 0.852010 |
| 5 | 0.751996 |
| 6 | 1.047832 |

Median paired ratio is **0.745354**, a **25.465%** descriptive reduction. The frozen gate required <=0.65 (at least 35% reduction) together with preserved observed progress and hard correctness. **That gate FAILS; 5 Hz remains HOLD.** The ratio of mode medians is a different statistic and is not substituted. In block 6 fewer calls actually cost more wall time. Per-call median there is 34.224 ms at 5 Hz versus 22.964 ms at 10 Hz.

Hypothesis, not causal finding: periodic sampling phase relative to the game tick, plus host scheduling, may explain why frequency alone does not predict blocking. This experiment does not isolate those contributors. Six paired restores provide no population reliability guarantee or calibrated confidence interval.

## 4. Closure and integrity checks

- **494/494** periodic/final acquisition brackets valid; **18/18** final brackets fixed and final values strictly agree with `score.json`.
- Exact accepted program hash, intent token, key sequence and expiry cause match in all 18 cases.
- **18/18** verified empty releases. Cutoff-to-verified-empty median **0.485981 ms**, range **0.321646-1.013574 ms**. Not a hard-real-time bound; admission-to-empty is only an interrupted-occupancy upper bound.
- **1102/1102** heartbeat commands dispatched; zero missed scorer periods and no detected pre-finish privileged scorer field delivery. No adversarial filesystem isolation claim.
- Offline replay checked **525** exact PNG/RGB hashes and typed/full observation identity, source hashes, all raw samples/events and recomputed summary.
- **30 tests** pass: 18 acquisition tests (including 64 finite clock orderings) and 12 corruption/validity tests on a copy of the retained real preflight. The latter require the evidence bundle.
- A separate standard-library numeric-ledger audit independently rederived all 494 brackets, 18 finals and the same paired ratio. Selected per-call durations and final clock endpoints are also retained in `results/endpoints.json` for small, repository-only replay.

This is not a paired timing benchmark of old versus repaired receipt code. The old defect is a deterministic ordering counterexample. No performance improvement is attributed to the bracket repair itself. True episode-end/death races and `save_fixture` failure paths are not exercised by these 18 nonterminal runs.

## 5. Measurement variables and unit check

| Field | 意味 | SI unit / representation | Definition / assumptions | Type |
|---|---|---|---|---|
| sample_started_ns | 取得開始時刻 | s / integer ns | Before the provider callable; common monotonic clock | Nonnegative integer scalar |
| sample_ns | 採点値の取得時刻 | s / integer ns | Stamped by provider within its acquisition | Nonnegative integer scalar |
| sample_finished_ns | 取得終了時刻 | s / integer ns | After the provider returns | Nonnegative integer scalar |
| refresh_started_ns, refresh_finished_ns | 更新呼出しの開始・終了 | s / integer ns | Before/after one-tic refresh; no CPU-time claim | Integer scalar timestamps |
| deadline_ns | 入力権限期限 | s / integer ns | Accepted owner deadline; fixed from runtime clock +3075 ms | Integer scalar timestamp |
| source tic | 情報源の更新世代 | 1 / tick count | Actual engine version indicator; provider-specific meaning | Nonnegative integer scalar |
| blocking ratio | 対応する2試行の更新待ち時間比 | 1 | Sum of 5 Hz durations divided by 10 Hz durations in same block | Nonnegative real scalar |

Unit check: differences use the same runtime clock, in ns; dividing by 1,000,000 yields ms. A ratio of two durations is dimensionless. Reported 1 ns clock resolution is not accuracy. Health, ammunition and kills are dimensionless game counts.

## H / T / D / C / U and successor

H: honest final acquisition envelopes remove the known defect; 5 Hz refresh may retain the scoped observation while cutting wall blocking by >=35%.
T: 30 tests, retained negative records, excluded preflights, 18 frozen real sessions, raw/pixel/ledger replay.
D: PASS versioned acquisition integration. FAIL cadence cost gate / HOLD optimization. No shared-runtime, general-policy or gameplay-speedup promotion.
C: game-tick phase, scheduling, observer-induced timing and a progress event near the sampling grid may dominate; changing freshness cadence can miss later events in other states.
U: one frozen local state, saved RNG, six restores per mode, one unpinned host, no frontier model, no real task completion. Combined uncertainty and coverage factor are not estimated.

Next one-variable question: at the SAME refresh rate and authority, does phase offset or bounded dephasing reduce wall blocking without worsening command responsiveness or missing progress? Do not simply lower frequency again or install a fixed Doom primitive as a generic interface.

Related fields: measurement science (source time vs acquisition), distributed systems (coherent stale reads), and real-time control (observation load vs input authority).
