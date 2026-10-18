# #6576 runtime-envelope invalidation A04 — first outcome

Decision: **PASS_RUNTIME_ENVELOPE_INVALIDATION_A04_SCOPED**.

This is fresh CPU-only synthetic construction/method evidence under Issue #6576. It does **not** consume or replace the frozen formal six-case T0 allocation and establishes no real input-release tail or safety guarantee.

## Frozen comparison

- 30 stationary streams, 30 declared-shift streams, 30 distribution-identical-but-undeclared shift streams.
- 1,024 samples/stream; shift index 512.
- Reference: Exp(scale=1).
- Shifted: 90% Exp(1) + 10% [8 + Exp(scale=4)].
- Sample detector: rolling 64, alarm at >=6 values above exact reference p99 `-ln(0.01)`.
- Declared-mode policy: NOT_ESTIMABLE from the first independently declared non-reference mode label.
- Diagnostic horizon: 16 post-shift samples.
- Deterministic cutoff diagnostic remains 8 synthetic units; statistical status never relaxes it.

## First formal result

Candidate invoked once, exit 0; reruns/replacements/tuning 0.

- 90/90 rows complete.
- Stationary sample-detector false alarms: 0/30.
- Declared-mode invalidation: exactly index 512 in 30/30 declared shifts.
- Metadata invention on stationary/undeclared streams: 0/60.
- Sample detector alarmed eventually in 30/30 shifted streams.
- Sample-detector delay from shift: median 62 samples, min 13, max 180.
- Only 1/30 shifted streams alarmed within the 16-sample diagnostic horizon.
- 23/30 shifted streams contained a reference-p99 exceedance inside the first 16 post-shift samples.
- 21/30 contained at least one value above the independent fixed cutoff 8 in that horizon.
- 22/30 satisfy the preregistered counterexample: sample alarm delay >16 and a p99 exceedance inside the first 16 samples, while declared-mode invalidation was already active.

The undeclared-shift streams use identical generated values to their declared counterparts but expose no mode change. The metadata policy therefore remains uninformed there by design; it does not infer hidden modes.

## Audit / corruption controls

Separate raw-only auditor: 90 rows, 905 checks, errors=[]; result decision reproduced. Ten effective copied-evidence mutations were all rejected: missing/duplicate row, bool seed, sample mutation, alarm mutation, mode schedule/alarm mutation, authority escalation, result-decision mutation and counterexample-count mutation.

## Interpretation

A statistical change detector can be useful diagnostically, but this finite counterexample shows it cannot be assumed to invalidate a stale reference-tail claim before a short deterministic deadline. When the system already knows it entered a different release path/mode, retaining that mode boundary and immediately marking the old tail estimate conditional/NOT_ESTIMABLE is stronger evidence than waiting for enough timing samples to accumulate. Conversely, if the mode is genuinely undeclared/unobserved, this metadata mechanism cannot detect it; no sampled method gets hidden-mode knowledge for free.

The detector was not optimized. A different statistic/window can be faster. The authored synthetic mixture is not a natural release distribution. This result is therefore a scoped evidence-contract result, not an argument that `W=64`, `K=6`, 16 samples, or this generator should be deployed.

## Scope limits

No EVT/GPD fit, TailID implementation, physical timer, XSync or neutral-state receipt, actual key release, watchdog execution, GUI/game/model/GPU, operational probability, worst-case bound, safety certificate, token/latency benefit, or product claim. Environment is the provided Linux execution container with standard-library CPython; it is not claimed WSLc/OrbStack/Docker image-attested.
