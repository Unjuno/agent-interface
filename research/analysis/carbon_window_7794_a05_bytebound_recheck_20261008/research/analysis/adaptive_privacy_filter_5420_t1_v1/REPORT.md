# Issue #5420 T1 — adaptive privacy-loss filter on a synthetic RR channel

## Disposition

`PASS_ADAPTIVE_FILTER_SYNTHETIC_RR_SCOPED` for the preregistered mechanism/accounting gate. This is not a DP claim about screenshots, OCR, tool traces, or user interfaces.

The one frozen OrbStack run completed 4,096 states in 2,048 paired neighboring-state fixtures and 20,480 policy rows. The adaptive epsilon filter never exceeded the 1.2 budget; the per-call, query-count, and non-stopping odometer controls all produced compositions above 1.2. Predicate-only release made no secret query and preserved the fixture's public-predicate task completions.

## Results

| Policy | Mean queries | Mean composed ε | Max ε | Episodes with ε > 1.2 | Distinguisher accuracy | Task completions |
|---|---:|---:|---:|---:|---:|---:|
| Static per-call authorization | 6.907 | 3.951 | 5.6 | 4,096 | 0.875610 | 2,050 / 4,096 |
| Global query-count cap (3) | 3.000 | 1.615 | 2.0 | 3,148 | 0.775635 | 2,050 / 4,096 |
| Symbolic odometer (no stop) | 6.907 | 3.951 | 5.6 | 4,096 | 0.875610 | 2,050 / 4,096 |
| Adaptive ε filter (limit 1.2) | 2.231 | 1.100 | **1.2** | **0** | 0.833008 | 2,050 / 4,096 |
| Predicate-only | 0 | 0 | 0 | 0 | **0.500000** | 2,050 / 4,096 |

The adaptive filter refused the next over-budget query in all 4,096 episodes and logged every admitted and refused decision. Every policy released the same secret-independent public task predicate; completion was 2,050 episodes for all five policies. In this finite corpus the filter's empirical transcript distinguisher accuracy (0.833) was below the no-stop odometer (0.876), but above the three-request count cap (0.776). Accuracy is a finite, seed-coupled simulator statistic—not a privacy bound, population estimate, or ranking independent of the chosen distinguisher.

## Mechanism and guarantee boundary

The only secret-bearing channels are explicitly defined binary randomized response with ε=0.4 and ε=0.8. The channel is adaptively selected from prior responses. The accounting increments are the exact per-response log-likelihood contributions ±ε. Under the specified randomized-response mechanism and adaptive composition, a filter that stops before the cumulative sum exceeds 1.2 enforces that mechanism-level bound. The executable corpus and independent audit check implementation behavior on these fixed seeded traces; they do not by themselves prove a production mechanism or validate any UI modality.

The task predicate is secret-independent by construction. Equal completion therefore demonstrates only that this particular toy task can use a minimized predicate instead of requesting the separate secret-bearing diagnostic. It does not show that predicate-only release preserves utility when a real task depends on the sensitive state.

## Audit and reproducibility

Independent raw-only audit: `PASS_RAW_AUDIT`, 4,096 inputs, 20,480 outputs, zero errors, four of four mutation controls rejected. Exact commands, environment, H/T/D/C/U, hashes, and raw JSONL are in [PLAN.md](PLAN.md), [EXECUTION.md](EXECUTION.md), and [SOURCE_MANIFEST.md](SOURCE_MANIFEST.md).

## Limits / next experimental boundary

No screenshot/OCR/tool-output mechanism, pixel sensitivity, user harm, side-channel, consent, cross-session linkage, or end-to-end utility was measured. Do not call this “DP for agent observations.” Next, preserve the same secret-neighbor test while changing one assumption at a time: hidden/public auxiliary identifiers, correlated repeated randomness, mechanism-mismatch or invalid epsilon metadata, safety-critical task predicates that actually depend on the secret, and redact/consent alternatives. Any real modality needs its own formal mechanism and neighboring relation before a privacy guarantee is claimed.
