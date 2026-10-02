# Hazard-shaped discretionary capture — T0

## H / T / D / C / U

**H.** Under a prospectively fixed nonuniform cue-onset distribution, an equal-count hazard-shaped discretionary capture schedule may improve expected detection of short transient cues versus uniform and phase-diversified schedules. The advantage should disappear/reverse under flat or inverted onset distributions. Mandatory sentinels remain identical and are never optimized away.

**T.** Exact-rational finite interval enumeration over onset ticks 0–11, two cue widths (1 and 2 ticks), deterministic capture-exposure brackets ±1/4 tick, and three equal-cost discretionary schedules A/B/C. Retain independent mandatory sentinel times in every arm; add a scoring-only enumerated oracle D. Score peaked, flat, and inverted distributions, every onset (including misses), delay, worst case, false positives, and max gap. Include unknown/zero hazard HOLD, all-budget-mandatory NOT_APPLICABLE, no-cue, and same-run-label leakage rejection. Candidate once; independent raw-only auditor once; retries 0.

**D.** `PASS_METHOD_SCOPED` iff exact oracle agrees for every schedule/distribution/width/onset; with the peaked selection distribution, C improves weighted detection by at least 0.10 absolute over **each** of A and B averaged equally over the two widths; flat and inverted controls are not advertised as wins (C must not strictly exceed both baselines); mandatory sentinel schedule is byte-identical; captures/count/cost match; no-cue false positives are zero; misses remain explicit and never become ABSENT/SAFE; controls and mutation checks pass. Else `FAIL_METHOD` or exact HOLD.

**C.** Source main `6cd70ad4bfad74e11658057bf024918bffb24add`. Pure Python stdlib rational interval enumeration, no model/GUI/input. Shared Docker/OrbStack lifecycle is unresolved (#5085/#626) and the engine was reported unresponsive; therefore no container was started. This T0 is explicitly an analytic finite method test and host computation avoids the shared runtime.

**U.** Onset weights are declared synthetic, not empirical or independently calibrated to a live task. Capture detection is deterministic interval overlap. No live cue, useful effect, GUI, task success, safety guarantee, or MAP01 benefit is inferred. A flat/inverted result tests misspecification only; it does not provide a bound on unknown real-world distribution shift.

## Freeze

`FIXTURE.json` fixes the distributions, schedules, sentinel times, exposure brackets, widths, costs and thresholds. Candidate selects no schedule using labels from scored cases. D is scoring-only. Freeze source hashes in `FREEZE.json` before candidate invocation.
