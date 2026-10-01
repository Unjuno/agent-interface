# Hazard-shaped discretionary capture — T0

## H / T / D / C / U

**H.** With a prospectively fixed nonuniform onset distribution, equal-count hazard-shaped discretionary captures may improve expected detection of short transient cues over uniform and phase-diversified captures; the advantage should vanish or reverse under flat/inverted scoring distributions.

**T.** Frozen exact-rational intervals: 12 possible cue onsets, cue widths 1 and 2, exposure brackets ±1/4 tick, identical sentinels `[0,5,12]`, three discretionary captures per A/B/C arm. A is uniform `[2,6,10]`; B is phase-diversified `[1,6,9]`; C is hazard-shaped `[2,3,8]` with one exploration/floor capture. D enumerates every legal three-center schedule as scoring-only oracle. Score peaked/flat/inverted distributions, every onset including misses, conditional detection delay, max gap, no-cue false positives, zero/unknown hazard HOLD, all-budget-mandatory NOT_APPLICABLE, and same-run-label leakage rejection. Candidate once, independent raw-only auditor once, retries 0.

**D.** `PASS_METHOD_SCOPED`. The separate exact-rational auditor matched all 216 onset metrics, checked equal costs and identical sentinels, confirmed the scoring-only oracle bounds all A/B/C schedules, retained every miss, and rejected 3/3 mutations. Under peaked weights, C's equal-width-mean detection exceeds A by `7/38` and B by `4/19`, both above the frozen `1/10` threshold. Under flat weights C ties A at width 1 and all arms tie at width 2; under inverted weights C is below both baselines. No-cue false positives=0. Zero/unknown hazard returns HOLD; all-budget-mandatory returns NOT_APPLICABLE; same-run-label schedule is rejected.

**C.** Main `6cd70ad4bfad74e11658057bf024918bffb24add`; CPython 3.14.5; standard-library exact fractions. T0 is analytical and no container/model/GUI/input is required. Shared Docker/OrbStack ownership remains unresolved, so no container was started. Source and thresholds are frozen in `FREEZE.json` before candidate invocation.

**U.** Onset weights are synthetic declarations (the peaked weights sum to 19), not measured task hazards. Detection is deterministic interval overlap. For the peaked fixture, width-1 detection is A `9/19`, B `8/19`, C `16/19`; width-2 is A/B/C `18/19`. The scoring-only enumerated oracle chooses `[3,7,9]` at `18/19` mean, while C is `17/19`. Flat control: width 1 A/C `9/12`, B `8/12`; width 2 all `11/12`. Inverted control: width 1 A `16/19`, B `15/19`, C `9/19`; width 2 A/B `18/19`, C `11/19`. No live cue-detection, useful effect, application/task benefit, safety guarantee, or MAP01 claim follows. Flat/inverted controls challenge a guessed schedule but cannot bound real distribution shift.

## Execution

Candidate: `python3 -B research/analysis/hazard_discretionary_capture_6086_t0_v1/candidate.py` — one invocation, exit 0, 3 arms × 3 distributions × 2 widths × 12 onsets, raw SHA-256 `bbb8b192c3e4ec2a50517208064b56a1d4d425fefc613a5e794a8124b2986ae2`.

Auditor: `python3 -B research/analysis/hazard_discretionary_capture_6086_t0_v1/audit.py` — one invocation, exit 0, 216 independently recomputed onset metrics, 3/3 mutation controls rejected, audit SHA-256 `09a0949ab2baed2b8118965a92c2419cd23f08608a913579968ef2cc7d1fb9c0`. Retry count 0. Exact first output is preserved in `results/t0/`; `RUN.json` records the invocations. No result from prior Issues or closed experiments is pooled or regraded.
