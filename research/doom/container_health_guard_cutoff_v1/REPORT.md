# Real MAP01 authority cutoff + health guard development study v1

Status: **development mechanism evidence only; not a formal allocation and not gameplay-efficacy evidence.**

## Question

Under a retained real ViZDoom/X11 MAP01 state where damage actually occurs while input authority is active, how should input authority end while a slow planner could still be pending?

This study deliberately tests simple boundaries in sequence rather than adding another large controller:

1. find an existing fixture with natural observable health change;
2. compare a precommitted InputOwner deadline with an explicit controller cancel at the same nominal boundary;
3. test whether a fresh observable health guard can stop authority earlier than the fixed deadline.

It does **not** test model quality, map navigation, or broad gameplay success.

## Immutable runtime / environment

- runtime source bundle commit: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`;
- source/wheels exported by Actions run `34973453255`, artifact `10398313098`;
- ViZDoom 1.3.0 / Freedoom MAP01 / skill 1 / `ASYNC_SPECTATOR` 35 Hz;
- private Xvfb/Openbox, visible 640x480 game;
- CPython 3.13.5, Linux 6.18.44 x86_64, AMD EPYC 9V74 80-Core Processor;
- affinity [0, 1, 2, 3, 4]; CPU frequency not pinned;
- model calls: **0**.

The exact development runner was executed interactively in the disposable container and was **not preregistered or source-frozen before outcome inspection**. Therefore all results below remain development evidence. Full raw outputs are hash-bound by `archive.json`.

## Discovery 0 — choose a damage-exposing retained fixture

`map01-threat-contact-v2` showed no health loss during a 4 s input-free coast. `map01-threat-contact-v1` exposed a natural `100 -> 97` health drop at roughly 3.15 s in the calibration run. Both fixtures independently reached an episode-finished/no-death state after about 4 s of coast, so this study uses only the earlier authority/release window and makes no map-clear claim from the fixture.

Selected condition: `map01-threat-contact-v1`, one held `Shift_L` key (no locomotion by itself), 5,000 ms requested hold, with authority boundary/guard before the fixture's later terminal state.

## Discovery 1 — fixed owner deadline vs explicit cancel

Three same-fixture matched seed pairs were retained, order D/C, C/D, D/C. Both arms used the same long `Shift_L` hold; the only intended difference was how authority ended at the nominal 3.5 s boundary.

| pair | deadline -> verified empty | cancel request -> verified empty | deadline - cancel | min health |
|---|---:|---:|---:|---:|
| 1 | 0.476 ms | 2.523 ms | -2.047 ms | 97 / 97 |
| 2 | 0.450 ms | 1.007 ms | -0.557 ms | 97 / 97 |
| 3 | 0.483 ms | 0.815 ms | -0.331 ms | 97 / 97 |

Medians: deadline **0.476 ms**, explicit cancel **1.007 ms**, paired deadline-minus-cancel **-0.557 ms**. Deadline was shorter in 3/3 pairs. All six arms exposed health `100 -> 97` and ended with verified empty input.

This difference is sub-millisecond-scale in the median and scheduler/host dependent. It supports deadline enforcement as a tight independent authority cap in this fixture; it is not a general speed claim.

## Discovery 2 — fresh health guard vs blind fixed deadline

For the same three seeds, a separate development arm kept a long lease but cancelled on the first **typed, controller-visible health observation below source health**. The already-retained fixed-deadline arms were reused as the comparator; they were not rerun.

| pair | health-guard accepted -> empty | fixed-deadline accepted -> empty | guard - deadline | damage capture -> empty |
|---|---:|---:|---:|---:|
| 1 | 3173.153 ms | 3499.820 ms | -326.667 ms | 14.734 ms |
| 2 | 3098.151 ms | 3499.914 ms | -401.763 ms | 13.560 ms |
| 3 | 3108.497 ms | 3500.031 ms | -391.533 ms | 14.731 ms |

Medians:

- fresh-health guard authority end: **3108.497 ms after acceptance**;
- fixed deadline authority end: **3499.914 ms**;
- guard-minus-deadline: **-391.533 ms**;
- damage-frame capture -> verified empty: **14.731 ms**;
- cancel request -> verified empty: **1.269 ms**.

The guard ended authority earlier in 3/3 pairs, by about 0.33--0.40 s in these first outcomes, because damage occurred before the blind 3.5 s cap. Every guard arm reached verified empty input.

## Interpretation

The evidence argues against treating **deadline** and **fresh guard** as competing mechanisms.

- The owner deadline supplies an independent worst-case authority lifetime even if higher-level control stalls.
- A fresh observable guard can terminate substantially earlier when the environment invalidates the continuation before that deadline.
- Explicit controller cancellation is the mechanism by which the guard requests the stop; the owner remains the independent component that verifies physical empty input.

The candidate architecture is therefore **guarded authority with a hard deadline cap**: `authority_end = min(observable_guard_failure, lease_deadline)`, with program-terminal lifecycle remaining separate from physical authority lifetime.

## H / T / D / C / U

**H.** A local observable invalidation guard can stop stale motor authority before a blind deadline, while the independent owner deadline remains the fail-safe upper bound.

**T.** One fixture-selection calibration, three matched deadline-vs-cancel seed pairs, and three fresh health-guard arms reusing the retained deadline comparators. Zero model calls. Same real MAP01/v13 X11 stack.

**D.** **PASS as development mechanism evidence.** All relevant releases are verified; deadline beats same-boundary explicit cancel in 3/3 pairs, and the health guard beats the later fixed deadline in 3/3 pairs. **No formal promotion and no gameplay-efficacy claim.**

**C.** The observed deadline-vs-cancel gap may be pure scheduler/IPC timing. The guard advantage depends on the typed health decoder/capture cadence and on this fixture's damage timing; another observable may be required for navigation or ammo/threat changes. The fixture later terminates without a death, so health loss here is an invalidation exposure, not a survival benchmark.

**U.** n=3, one key, one saved state, one host family, no frequency pinning, interactive development runner not preregistered, and no frontier-model wait. Full raw archive: **121,794,034 bytes**, SHA-256 `c618494c61813ca7844249e2f038593b1a0e11d1a083d238db20bd83f1431187`.

## Next gate

Do not add another timing micro-variant. The next informative integration is to compose this rule into the existing bounded-recovery planner-wait path: retain the independent deadline, allow only explicitly authorized recovery, and cancel it on a current typed invalidation signal. Then use the independent scorer to distinguish helpful continuation from harmful stale input. That successor must be separately frozen before a model-in-loop or formal efficacy allocation.
