# #6576 runtime-envelope invalidation A04 — frozen plan

Allocation: `EXTREME-TAIL-6576-RUNTIME-ENVELOPE-A04-20261006-001`.
This is fresh CPU-only construction/method evidence. It does not consume formal six-case T0.

## H
When an independently declared release mode changes, the reference-tail claim becomes conditional immediately. A sample-only rolling exceedance alarm may detect the shift later and therefore cannot be treated as protection for a 16-sample diagnostic horizon. If the mode change is not declared, metadata logic must not invent it.

## T
Standard-library CPython. Three conditions × 30 fresh seeds = 90 rows, each 1,024 nonnegative synthetic delay samples. Shift index 512. Reference samples are Exp(scale=1). Shifted generator uses 90% Exp(1) plus 10% `8 + Exp(scale=4)`. Only `declared_shift` exposes mode metadata at index 512; `undeclared_shift` has identical distribution but retains reference metadata. Reference p99 is exact `-ln(0.01)`. Sample detector: rolling 64 samples, alarm at >=6 p99 exceedances. Diagnostic horizon: 16 post-shift samples. Deterministic cutoff diagnostic: 8 units, never relaxed by a statistical policy. Formal seeds 65764101..65764130. One candidate invocation, one separate audit; no rerun/replacement/tuning. Construction seeds 65764001..003 are excluded.

## D
PASS_RUNTIME_ENVELOPE_INVALIDATION_A04_SCOPED iff all 90 rows are complete; declared-mode invalidation is exactly 512 in all declared rows and absent in stationary/undeclared rows; stationary sample-alarm false alarms <=1/30; and >=1 declared-shift row has sample-alarm delay >16 while containing a p99 exceedance in the first 16 post-shift samples. Otherwise FAIL/HOLD. No policy grants input authority or task success.

## C
A different online detector can be faster; this does not prove optimality. Explicit mode metadata is additional system evidence. The authored mixture is not a natural release distribution.

## U
No EVT/GPD/TailID fit, real timer, release endpoint, physical key-up, XSync/neutral measurement, real watchdog, population rate, safety/worst-case, model or product claim.
