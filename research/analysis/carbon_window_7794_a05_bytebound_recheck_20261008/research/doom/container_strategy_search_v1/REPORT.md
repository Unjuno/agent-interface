# Container MAP01 strategy search v1

Status: **development candidate found and transferred to one derived state; no broad efficacy or navigation claim.**

Base: `5ea234d204e776774a6cdd46972cc0daa9b79766`. Issue #117. Runtime bytes came from the retained local source bundle and were not modified. ViZDoom 1.3.0 / Freedoom MAP01 / `map01-threat-contact-v2`; CPython 3.13.5, Linux 6.18.44 x86_64, Intel Xeon Platinum 8573C, affinity 0--4, host clock not pinned. Zero model calls.

## Search procedure

The goal was not to construct a new runtime but to find a useful bounded motor policy in the real container. A direct ViZDoom API screen was used only for development candidate selection. Candidates were then run through the actual `session_map01_v13.py` X11/Executor/InputOwner path. X11 runs submitted a long hold but bounded physical authority with `valid_until_ns`; independent score and verified empty release were retained.

The API screen compared constant button combinations for 2.8, 3.2, 3.6 and 4.0 seconds. It suggested plain `attack` and `back+left+attack` as useful candidates. API results are not counted as interface evidence.

## Real X11 results

Plain `attack` with owner-deadline authority was non-monotonic across fresh sessions:

| authority | kills / 3 | verified release | median deadline -> verified empty |
|---|---:|---:|---:|
| 3075 ms | 2/3 | 3/3 | 1.430 ms |
| 3200 ms | 2/3 | 3/3 | 0.552 ms |
| 3500 ms | 1/3 | 3/3 | 0.488 ms |

Therefore a fixed monotonic "minimum kill threshold" is rejected. Async enemy state / scheduling and action geometry matter.

The composite `back+left+attack` candidate at 3075 ms produced **3/3 independent kills**, zero deaths, no map exit, health 97 -> 97 in all three sessions, ammo 48 -> 40, and 3/3 verified releases. Physical authority ended at about 3068.8--3073.2 ms after admission; deadline-to-verified-empty was 0.552--0.605 ms (median 0.586 ms).

A one-sample-per-cutoff sweep of the composite candidate gave:

| authority | kill | deadline -> empty |
|---|---:|---:|
| 2500 ms | 0 | 0.722 ms |
| 2750 ms | 1 | 0.713 ms |
| 2850 ms | 0 | 1.549 ms |
| 2950 ms | 1 | 0.588 ms |
| 3050 ms | 1 | 0.412 ms |

Again this is non-monotonic and not a rate estimate. It only bounds promising regions for a later matched allocation.

A separate same-fixture four-arm development check showed coast 0 kill; ordinary 3000 ms `attack` completed with one kill but physically retained input for about 3083 ms; 3000 ms deadline and 3000 ms explicit cancel both had zero kills and verified release. This exposed an important confound: historical capture-coupled overshoot can sometimes cross a useful-action boundary, so eliminating overshoot is not automatically an efficacy improvement.

## Derived-state transfer

A second state was created from the retained v2 fixture through the same real X11 session: hold `d` for 650 ms, coast 350 ms, then `save_fixture`. Its save SHA-256 is `d13e7b96f34afe512a827bfbcda811092aa26dde0154e235f0191cb2ae3e6c05`, episode tic 1417. This is a nearby derived MAP01 state, not an independent map/domain.

At the same 3075 ms owner deadline:

| policy | kills / 3 | deaths | verified release | deadline -> empty range |
|---|---:|---:|---:|---:|
| `attack` | **0/3** | 0/3 | 3/3 | 0.277--1.157 ms |
| `back+left+attack` | **3/3** | 0/3 | 3/3 | 0.470--0.583 ms |

The composite candidate therefore reproduced 3/3 on both the original and derived state, while plain attack dropped from 2/3 on the original state to 0/3 on the derived state. This is useful transfer evidence inside one MAP01 neighborhood, but not a general gameplay policy result.

## H / T / D / C / U

**H.** A simple motion+attack policy can generate useful independent progress during a bounded authority window while owner deadlines keep release tightly bounded.

**T.** Development API screen followed by real X11 deadline sweeps, three fresh replications of the best composite candidate, and one nearby-state transfer with three fresh sessions per arm. Score fields, typed health/ammo where collected, terminal status and owner release were retained.

**D.** `back+left+attack` at 3075 ms is **PROMOTED TO A MATCHED DEVELOPMENT CANDIDATE**, not production policy. Plain attack duration-threshold reasoning is rejected. The derived-state transfer favors the composite 3/3 vs 0/3. No navigation/exit efficacy claim.

**C.** The result may still be specific to one local MAP01 region. More authority can be worse because movement changes aim/line-of-sight. API screening uses a different control path. An expected `expired` terminal must not be confused with stale-authority failure in production semantics.

**U.** n=3 per replicated point, two nearby states, one host, no planner/model, no positive map-exit result, and no confidence interval. Scheduler jitter and asynchronous game state dominate. Health did not change in selected runs, so survival benefit is unproven.

## Next experiment

Stop tuning deadline duration on this fixture. Run a matched randomized comparison of `attack` vs `back+left+attack` on multiple independently derived MAP01 states, keeping the same owner deadline. Primary endpoint: independent kill/progress event before authority expiry; secondary: ammo cost, health change and release latency. If the composite continues to transfer, only then connect it to actual planner-wait windows. Do not spend time on packaging until this discriminator is closed.
