# Equal-count scorer phase search and one-shot rephasing

**Decision: HOLD both stage-1 fixed schedules under the complete frozen gates; retain stage-2 one-shot rephasing as a scoped evaluator candidate, not production.** Issue #149.

Publication base: `a1ea4cbfac735eafb1f8901dd6c32a890bed015c`. Immutable real runtime: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`. Acquisition envelope code is copied byte-exact from PR #147 (`775ee2cc2df4e03d2c1ec40ad83052ddeb187b06`). Historical runtime, workflow, allocations and prior results are unchanged.

## Experiment 1: change request timing, not observation count

The previous 5 Hz trial did not pass its cost gate. This successor instead holds the number of refreshes fixed. All arms perform one common refreshed acquisition, 30 scheduled one-tic refreshes, then one final acquisition. The completion of the common acquisition is the schedule origin. It is an **estimate**, not an observed true engine-tick phase.

Uniform uses 100 ms request intervals. Early/late alternate nominal three/four 35-Hz tic intervals (two requests each 200 ms), with 0.15/0.75 tic offsets from estimated boundaries. The early offsets start at 90.000, 204.286 ms; late at 107.143, 221.429 ms. The schedule is finite; late wakeups skip slots rather than fabricate catch-up samples. Complete analysis requires all 30 slots to have actually finished before the unchanged owner cutoff.

Freeze `6b2ee9398bc964810be79740d08112b32b22807e` precedes all 18 measured cases. Three arms times six restores use every arm-order permutation once. Identical `[s,a,space]`, requested 5000 ms hold, 3075 ms owner cutoff, threat-contact-v2 save, scorer fields, and nominal 20 Hz heartbeat command load. Expected terminal is `expired`, never relabelled completed.

| Arm | Blocking median [range], ms | Median per-case heartbeat p95, ms | Pre-cutoff positive observation | Final kills |
|---|---:|---:|---:|---:|
| Uniform | 645.827 [577.838, 668.396] | 24.013 | 6/6 | 6/6 |
| Early | 732.469 [713.325, 749.002] | 22.636 | 6/6 | 6/6 |
| Late | 222.639 [197.313, 865.470] | 6.115 | 6/6 | 6/6 |

Blocking is the sum of **30 scheduled refresh-call wall durations**, not CPU time, total control time, or latency to the true effect. Calibration/final calls are excluded. Every recorded refresh remains an explicit evaluator intervention (`advance_action(1, True)`), never a policy button-selection call or claimed passive observation. Official API background: https://vizdoom.farama.org/api/python/doom_game/ . Conclusions come from installed 1.3.0 observations, not from assuming current docs describe every timing detail.

Early/uniform median paired cost ratio: **1.149684** (14.968% worse). Late/uniform: **0.341025** (65.898% descriptive reduction), but block 4 is **1.497772**: late 865.470 ms versus uniform 577.838 ms. Keeping only the first three pairs would conceal this regression.

A second reason prevents full-gate promotion: uniform block 5 ended with HUD ammo **41**, while both other arms ended at **40**. All began at 48; all health stayed 97 and all had one kill, zero deaths, no exit. The frozen gate required exact paired score/health/ammo equality, not merely equal kills. Thus **late passes its cost subgate but FAILS the full gate**. Earlier issue commentary that says the median-cost gate passes must not be read as complete acceptance. The raw final screenshots are retained and pixel hashes checked; causal attribution of this one-round difference is not established.

## Experiment 2: one bounded correction from observed blocking

Stage-1 failure motivated a separate freeze, not retuning its offsets or rerunning an allocation. Both arms start from the same late schedule. They use either no additional origin shift or a predeclared 12 ms schedule shift. This is an injected scheduling perturbation, not a claim of actual hidden engine phase.

Static does nothing further. Rephase inspects the **full duration of its first scheduled acquisition**. If it exceeds half a nominal tick, it shifts subsequent requests later by that duration minus one-quarter tick, capped at 20 ms. It does this once only. It never reads kills, health, fixture ID or reward to choose timing; uses no busy-wait and does not increase count or authority. Both modes have the same calibration/final work and identical delay condition.

Freeze `e1890ee06bc7ad5633194fb007fa6fac3333ca55` precedes all 12 stage-2 cases. Three matched pairs per origin-shift condition; pair order alternates, not fully counterbalanced within each three-pair subgroup. The comparison is new; it is not a paired causal contrast with stage 1.

| Origin shift | Static blocking median, ms | Rephase blocking median, ms | Median paired ratio |
|---|---:|---:|---:|
| 0 ms (3 pairs) | 217.978 | 208.462 | 0.936192 |
| 12 ms (3 pairs) | 720.315 | 237.819 | 0.331309 |

Across all six paired ratios the median is **0.633797**, a **36.620% descriptive reduction**. This is not the ratio of the all-arm medians. The frozen <=0.8 cost gate and <=1.1 gate within each shift group both pass. All 12 final scores, health and ammo agree pairwise; every case detects a positive event before cutoff, samples 30 requested slots and verifies empty input. Maximum measured sample gap stays under the frozen 250 ms ceiling.

All three unshifted candidate cases made zero correction. All three shifted candidates corrected once by **16.887, 15.977 and 16.529 ms**. The correction rule is not a universal controller: a busy provider, variable period or delayed anchor could produce a different response.

**Important negative:** lower cumulative blocking is not proved to improve arbitrary command latency. Across stage 2, the median of per-case heartbeat p95 values is **3.760 ms static versus 4.839 ms rephase**. The heartbeat's phase relative to blocking matters. No command-response speedup is claimed, and no tail-bound follows from these samples.

## Conditions and evidence

AMD EPYC 9V74; affinity CPUs 0-4; unpinned/uncontrolled shared-host frequency. CPython 3.13.5; Linux 6.18.44 x86_64/glibc 2.41; ViZDoom 1.3.0; NumPy 2.5.3; Pillow 12.3.0; python-xlib 0.33. Private Xvfb/Openbox 1280x800, visible 640x480 Freedoom MAP01, ASYNC_SPECTATOR 35 tics/s, skill 1, saved threat-contact-v2 RNG. These are repeated restores of one scene, not independent maps. Zero model calls and zero engine API action selection.

The restored bundle SHA256 is `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`: 2592 source entries and 12 wheel hashes verified. Both setup-only preflights pass and are excluded. All consumed measured allocations ran once, no live retries.

- **30/30** real-engine comparison cases pass source/action/intent/deadline/release checks.
- **960/960** periodic/final acquisition brackets; **30/30** final values agree strictly with score.json.
- All 900 scheduled refresh requests finish before cutoff; no missing schedule slots.
- **1831/1831** heartbeat commands retain exact identity/order and are dispatched.
- Cutoff to independently verified empty: median **0.513954 ms**, range **0.310670-0.834982 ms**. This is not a hard-real-time bound. Admission-to-empty is only an interrupted-occupancy upper bound.
- **883** exact RGB observation hashes and typed/full-frame identities replay successfully.
- 41 tests pass before stage 1; 46 before stage 2; six post-outcome stage-2 corruption checks bring the final suite to **52**. These counts are not interchangeable.
- Independent standard-library ledger audit rederives all 960 integer brackets, 1831 heartbeat timings, all schedules, final values and paired blocking ratios without importing experiment analyzers or scheduler code.

## Variables, units and conditional scope

| Field | Meaning | SI / stored unit | Definition and domain | Type |
|---|---|---|---|---|
| anchor_ns | Common acquisition completion; estimated origin | s / integer ns | Same process monotonic clock; not actual engine boundary | Integer scalar timestamp |
| scheduled_ns, sample_started_ns, sample_finished_ns | Intended/requested and actual acquisition endpoints | s / integer ns | Ordered nonnegative same-clock times | Integer scalar timestamps |
| sample_ns | Payload acquisition time | s / integer ns | Inside full acquisition bracket; not exact game event time | Integer scalar timestamp |
| schedule_index | Finite calibration/measurement slot | 1 | 0 calibration, 1..30 measured, final separate | Integer identifier |
| bootstrap_shift_ns | Declared stage-2 origin error | s / integer ns | 0 or 12000000, equal within pair | Integer scalar |
| correction_ns | One forward correction | s / integer ns | 0..20000000; from first acquisition wall duration only | Integer scalar |
| refresh_started_ns, refresh_finished_ns | Explicit refresh-call bracket | s / integer ns | Nested inside acquisition; wall blocking, not CPU time | Integer scalar timestamps |
| tic | Engine/state generation indicator | 1 | Monotonic sampled tick within this episode; nominal 35 Hz | Integer counter |
| heartbeat timings | Command write and dispatch endpoints | s / integer ns | Same host monotonic clock; empirical p95 is nearest rank | Integer scalar timestamps |
| score/health/ammo | Game outcome and observable HUD values | 1 | Counters/booleans, not SI physical quantities | Integer/Boolean scalars |

Unit check: subtract same-clock nanoseconds, divide by 1000000 to report milliseconds; ratios divide times with the same units and are dimensionless. Reported 1 ns clock resolution is not 1 ns accuracy. No calibrated combined uncertainty or coverage factor is available; empirical ranges and counterexamples are retained.

## H / T / D / C / U and next discriminator

H: timing phase can affect fresh observation cost at equal count; one bounded measured-duration correction can improve robustness to a declared origin offset.
T: two hash-frozen finite stages (18+12), two excluded preflights, exact raw replay and negative controls.
D: HOLD fixed early/late for complete stage-1 gates; scoped PASS stage-2 rephasing. No shared-runtime rollout, faster-kill or general-interface performance claim.
C: estimated phase, different interval pattern, scheduling/rendering drift, unknown provider work, injected rather than natural offset, one-round stage-1 outcome discrepancy, heartbeat phase and saved-world geometry.
U: one host/scene, three pairs per stage-2 perturbation cell, no planner/model, no independent reset of world RNG, observer intervention and source-acquisition/event-time distinction.

Next single question: with unpredictable command arrival times at fixed acquisition count, does the lower-blocking candidate reduce **command latency**, or does sampling-phase coupling erase the benefit? Do not add a gameplay selector or another runtime abstraction until that discriminator is measured.

Related domains: real-time scheduling (interference and service timing), measurement science (observer cost and acquisition envelopes), and distributed systems (provider freshness versus local receipt time). The generalizable candidate is bounded timing adaptation using provider response duration, not a hard-coded Doom movement or a universal 35-Hz assumption.
