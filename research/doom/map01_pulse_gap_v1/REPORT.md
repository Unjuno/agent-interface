# MAP01 pulse-gap experiment: application-recognized segmentation is not native release

Task `MAP01-PULSE-GAP-20260917-001`; Issue #649; direct follow-up to #628 / PR #645 and #480.

## Disposition

**SUPPORT_GAP_DEPENDENT_TURN_SEGMENTATION_SCOPED**. Fourteen fresh first-outcome sessions completed. The frozen independent audit has zero integrity/source errors and no omitted game tic. Increasing only the release settling from 10 to 100 ms made all six long-gap cases appear as six separate engine-observed turning episodes. The predeclared episode-increase gate passed in five of six matched pairs; paired median short-minus-long angular displacement was 38.671875 degrees.

This is a scoped input/effect diagnostic, not precision-control promotion, a closed-loop controller, natural threat exposure, a survival result or a MAP01 clear. The engine action/yaw trace is evaluation-only and never enters the fixed input worker.

## Issue alignment and roadmap

Read current #59, #104/#105, #480 and active Issue state before selecting the experiment. #626 owns threat/deopt real-game composition and #629 owns planner/reanchor admission; their files and allocations are untouched. This rung addresses #480's observed fixed-macro limitation, rather than introducing another macro language or duplicating the threat-control work.

The executed roadmap was: verify the pinned runtime closure; use at most two excluded construction sessions to check setup/telemetry; freeze source/audit/schedule; run the bounded first-outcome block; independently audit retained evidence; publish the exact data and one successor question. Shared runtime, workflows, release and site files are unchanged.

## H / T / D / C / U

**H (preregistered):** With six 190 ms Right pulses fixed, extending the requested released interval from 10 to 100 ms increases distinct game-observed turn episodes and reduces excess angular displacement. A change supports an input-consumption/time-history explanation, but does not uniquely prove that X11 events were lost.

**T:** Six matched seeds 993710..993715, alternating arm order, plus an initial and a final no-input control: 14 fresh private Xvfb/Openbox/ViZDoom sessions, one per outer container invocation. Two construction sessions on seed 993700 are excluded. No model, ATTACK, forward navigation, direct game action vector, pause, save-state or automap. Normal MAP01, skill 1, ASYNC_SPECTATOR, 35 tics/s. A fixed-input worker uses the exact retained InputOwner-v10 adapter; the evaluator samples `advance_action(1, True)`, `get_last_action`, yaw and game tic separately. Sampling does not grant controller access to hidden game state.

**D (frozen before formal):** All integrity gates must pass. Any omitted game tic or missing active-action exposure gives HOLD_TELEMETRY, not assumed neutral input. Support requires a long-minus-short episode increase of at least two in at least four of six pairs AND paired median short-minus-long absolute yaw of at least ten degrees. Otherwise retain NO_DISCRIMINATING_GAP_EFFECT_SCOPED. An unexpected integrity failure stops the block. No rerun, replacement, extension or threshold tuning.

**C:** Longer gaps can reset game turn history/acceleration, alter input sampling phase or add settling. Complete sampled tics are not a log of every underlying X11 event or a guarantee that every within-tic transition was processed. The later explanatory model below was inspected after measurement and is not an independent confirmatory result.

**U:** One software/backend/map configuration; uncontrolled host scheduling/frequency; roughly 28.57 ms game-tic granularity; phase-dependent input sampling. Six pairs are diagnostic, not a population reliability estimate. No calibrated combined measurement uncertainty or coverage factor is claimed. No threat, survival, model-cost, generic angle-accuracy or product-support promotion.

## First formal outcomes

Each arm/seed row is one fresh session. Episode counts are contiguous nonzero TURN_RIGHT runs in the evaluator's game-action trace, not counts of native key-down calls. Each active session emitted exactly six native pulses.

| Seed | Short-gap episodes | Long-gap episodes | Short absolute yaw (deg) | Long absolute yaw (deg) | Short minus long (deg) |
|---:|---:|---:|---:|---:|---:|
| 993710 | 2 | 6 | 126.5625 | 91.4062 | +35.1563 |
| 993711 | 5 | 6 | 89.6484 | 91.4062 | -1.7578 |
| 993712 | 2 | 6 | 126.5625 | 87.8906 | +38.6719 |
| 993713 | 2 | 6 | 126.5625 | 87.8906 | +38.6719 |
| 993714 | 1 | 6 | 138.8672 | 87.8906 | +50.9766 |
| 993715 | 1 | 6 | 138.8672 | 87.8906 | +50.9766 |

The contrary pair 993711 is retained: its short-gap trace already segmented into five episodes, and long-gap yaw was 1.7578 degrees larger. Do not report universal per-pair reduction.

Short-gap yaw median 126.5625 degrees, range 89.6484..138.8672; episode median 2, range 1..5. Long-gap yaw median 87.8906 degrees, range 87.8906..91.4062; all six episode counts are 6. Five of six pairs meet the episode-increase gate. Paired median angular reduction is 38.671875 degrees.

Both no-input controls have zero task pulses, zero engine turning samples and zero yaw change. All 14 initial/final independent X11 keymaps and pointer-button checks are neutral. All 86 native release records pass, including 14 explicit final releases. All 876 sampled game states have consecutive tics and matched state/episode tic; omitted tics are zero. All sessions remain alive, unfinished and health 100; this is not hazard-exposure evidence.

## Time and effect are separate outcomes

Input-worker elapsed time runs from worker start (including a common 100 ms initial coast) through its six pulses/settles and explicit final release. It excludes game startup, screenshot capture and evaluator final coast. Short-gap median is 1310.494 ms (1307.881..1313.389); long-gap median is 1851.171 ms (1848.560..1852.709). Difference of medians is **540.677 ms**, not a speedup.

The unchanged adapter settles after each of the six calls, including the last call. Therefore the nominal added requested settling is 540 ms, although there are only five between-pulse gaps. The manipulated factor is the `settle` argument on all six calls, not a falsely claimed five-gap-only change.

Requested down dwell is 1140 ms in both arms. Down-acknowledgement to up-request sums are short median 1140.815 ms (1140.683..1144.621) and long median 1142.262 ms (1140.866..1144.316). These are controller/owner receipt endpoints, NOT exact physical occupancy or game-consumed key-up timing. Smaller angular dispersion cannot be credited to shorter requested down dwell.

## Posthoc explanatory observation, not a second formal hypothesis

After the frozen audit, `analyze_turn_history_posthoc.py` examined the retained traces without new game execution. A model using 1.7578125 degrees per active tic for the first five consecutive turning tics, then 3.515625 degrees per active tic, and zero on neutral tics, fits all 14 traces. The maximum per-step residual is about 8.35e-8 degrees; no sample exceeds the descriptive 1e-6-degree tolerance.

Those constants, the five-tic breakpoint and the tolerance were selected/inspected after seeing the data. This is an empirical explanatory fit, not preregistered evidence, a new precision guarantee, or source-verified ViZDoom internals. The finite trace is consistent with continuity-dependent turn acceleration/reset: a short physical release can leave game-observed turning continuous, while a longer gap separates episodes and repeatedly returns them to the low-increment regime. Do NOT conclude that the OS failed to deliver release, or that all game event handling is identified.

A 100 ms gap is therefore not promoted as the final control solution. It trades wall time for more consistently separated application effects in this block. The next focused question is whether the five-tic history model predicts held-out pulse durations/phases with the gap and input owner fixed; no parameter sweep or new macro DSL is justified here.

## Variables and unit check

| Field / symbol | Meaning (Japanese) | SI unit | Definition / domain / assumptions | Type |
|---|---|---|---|---|
| requested_dwell_s | 1回の押下要求時間 | s | 0.19 for each of six active pulses | real scalar |
| requested_gap_s | 各呼び出し後の解放待ち時間 | s | 0.01 or 0.10; includes the final call's settle | real scalar |
| begin_ns, end_ns, input_ack_ns, up_started_ns | 観測・受付・解放要求の時刻 | s, encoded ns | monotonic integer clock; no wall-clock mixing | integer scalars |
| tic, state_tic | ゲーム更新刻み | 1 | consecutive integer game ticks at nominal 35 per second | integer scalars |
| action | ゲームが返す直前の操作 | 1 | two binary entries ordered TURN_LEFT, TURN_RIGHT; evaluator-only | length-2 vector |
| observed_turn_episodes | 連続した旋回区間数 | 1 | number of observed zero-to-nonzero runs; no imputation of missing tics | integer scalar |
| yaw_deg | 評価専用の方向角 | rad, stored deg | circular differences reduced to [-180,180); converted with pi/180 when SI needed | real scalar |
| consecutive_turn_tics | 同一旋回区間内の連続更新数 | 1 | posthoc streak count, reset only at sampled neutral action | integer scalar |
| slow/fast increment | 後解析の角度増分 | rad per game tic | stored as 1.7578125/3.515625 deg per tic; posthoc only | real scalars |

Unit check: 190 ms is 0.19 s and six requested dwells total 1.14 s. Six additional 90 ms settles total 0.54 s. Game ticks are not wall-clock seconds; observation gaps are evaluated in tic counts. All primary yaw thresholds and wrapped differences use degrees consistently; converting both to radians preserves decisions. A degree-per-tic increment is not silently compared to degrees per wall-clock second.

## Source, environment and construction retention

Publication BASE `5d85577dd3556725bfddf6a88e379e783a13ead0`. Source-first freeze `6ec8c670ad819ffbdf7d42b3251d24c9496a4328`; archive SHA256 `93b1c0a205c8f2a051a9fb4e7b0800933e0c97ca19789dc33f439140d9e5e5c9`; Base64 Git blob `e5d1befd4549a37b3d6ed5e8f0d4b13f4876f3ce`. Exact common.py adapter Git blob `d349f0f303c829b8dee8a6543bc9ee83b31ae5ba`. No runtime rebase onto moving main.

Runtime artifact 10398313098 has SHA256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`, runtime BASE `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`. All 2592 manifest source files and all 12 offline wheels matched their hashes; full closure installed in a private venv. CPython 3.13.5, ViZDoom 1.3.0, python-xlib 0.33, NumPy 2.5.3, Pillow 12.3.0. Linux 6.18.44 x86_64/glibc 2.41; AMD EPYC 9V74 with affinity CPUs 0..4, frequency uncontrolled. Xvfb 2:21.1.16-1.3+deb13u1; Openbox 3.6.1-12+b2. One game plus fixed-input and input-owner worker threads per serial case; no GPU claim.

Construction c00-short observed one episode/138.8672 degrees; c01-long six episodes/87.8906 degrees. Both excluded cases passed setup/integrity, and no gap/dwell/policy/scientific-gate tuning followed. Nine deterministic tests and compile passed before formal and the same tests passed afterward. Source files remain byte-identical to the premeasurement freeze. Process audio/Xauthority/TERM warnings are retained rather than suppressed; they did not produce scored setup or release failure.

## Evidence and independent checking

GitHub retains the nine-file frozen source archive and all 56 exact formal JSON texts (14 results, starts, cleanups and invocation receipts) in three reversible XZ/Base64 parts. Raw JSON-map SHA256 `90cc295c0be64c79b7b3efffac8a484acd40ebcb42cc56320a8ddf4c4c55507d`; XZ SHA256 `f6195f737c57cda745bd1ce1b847daa86f8d278eb8a3b6f6b61873d918b085ed`. The four remote source/data blob identities matched local bytes after publication.

`python restore.py NEW_DIRECTORY` verifies exact digests and file closure before restoring 9 source files and 56 formal JSON files. It refuses an existing output and never launches a game. This JSON restoration deliberately does not contain PNGs. The complete 32 PNGs, process logs, two excluded construction cases, source, original audit, corruption checks and posthoc scripts/results are in the separate conversation-retained `map01_pulse_gap_649_full_evidence.tar.xz`; its identity is recorded in PUBLICATION.json. The full frozen PNG audit requires that archive, not the GitHub JSON alone.

The auditor recomputes episode/yaw metrics from traces, validates native input count/content/time/release links, independent keymaps, source hashes, game lifecycle and PNG hashes. Seven copied-evidence corruptions are rejected. An eighth control deletes a sample and correctly yields telemetry HOLD without inventing a neutral state. The postformal verifier is a retained-copy check, not an eighth rejection or a formal rerun. Independent means separate checking code, not an external reviewer or another author.

After extracting the full archive, verify MANIFEST.json and run the frozen auditor against the extracted source/formal directories with a new output path. VERIFICATION.json records the actual reconstruction, test and byte-identity checks. No retained live allocation is rerun to verify publication.

## External API semantics inspected

Farama's official DoomGame reference documents `get_last_action()` as the last performed action ordered by available buttons and useful for spectator modes: https://vizdoom.farama.org/main/api/python/doom_game/

The original ViZDoom tutorial describes asynchronous game time continuing independently and `advance_action` waiting for the next frame: https://vizdoom.cs.put.edu.pl/tutorial

These references justify API use only, not our measured result or the posthoc acceleration model. No retrieved engine source is claimed as confirmation of that model.
