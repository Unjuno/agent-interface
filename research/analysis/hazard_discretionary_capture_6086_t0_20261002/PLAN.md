# Issue #6086 T0 — hazard-shaped discretionary capture

## Frozen H / T / D / C / U

- **H:** With a valid exogenous peaked onset distribution and equal discretionary exposure budget, concentration near the peak improves weighted short-cue detection over uniform and phase-diversified schedules. Under flat or inverted/misspecified weights the hazard schedule must not be advertised as a win.
- **T:** Exact rational enumeration over cue onsets 0..12 in 1/2-unit steps; cue widths 1/2 and 1; capture exposure brackets of 1/2; three discretionary brackets per policy; fixed sentinel times {0,6,12}. Policies: uniform starts {1,5,9}; phase-diversified {2,6,10}; hazard-shaped {4,5,6}; scoring-only oracle selects the best three starts on the 1/2 grid. Onset distributions: flat weight 1; peaked weight `max(1, 12 - 2*abs(onset-5))`; inverted/misspecified weight `1 + 2*abs(onset-5)`. A cue is detected only when a capture exposure interval intersects its half-open cue interval. All outcome arithmetic uses exact fractions. An independent implementation exhaustively checks each onset/exposure pair.
- **D:** `PASS_METHOD_SCOPED` only if at both widths the peaked-distribution hazard detection exceeds uniform and diversified by at least 1/10 absolute weighted probability; flat and inverted controls do not show hazard superiority over both comparators; sentinels and capture counts are identical; and exhaustive candidate/oracle outcomes agree. Otherwise retain FAIL/HOLD with no tuning or retries. No-cue stays NO_CUE; a miss never means ABSENT/SAFE. If all budget were mandatory, discretionary policy is NOT_APPLICABLE.
- **C:** Event subscriptions/latches or simple phase diversification may dominate; exposure and onset phase may be dependent; schedule effects may be artifacts of a guessed hazard.
- **U:** Authored onset distributions, deterministic synthetic exposure, no real phase-clock calibration, no render jitter, no model/GUI/input, and no safety guarantee or task benefit. Mandatory sentinels are held outside the allocation and never weakened.

The full finite input and scoring gates are frozen in `freeze.json` before running either evaluator.
