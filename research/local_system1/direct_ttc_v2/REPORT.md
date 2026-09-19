# Direct TTC v2 first outcome

Decision: `HOLD_TTC_SAFETY_OR_TRANSFER`.

Scientific source is byte-identical to #905 (`a34471ea...`). Fresh case IDs/seeds 9061701..9061704; each invoked once, reruns/replacements/tuning0. Aggregate invocation1. Independent audit PASS/errors[].

Direct TTC is competent and non-degenerate: ordinary accuracy 99.951-100.000%, stress 98.804-99.072%, all four exit depths used. Mean normalized compute is 0.570-0.585 ordinary and 0.710-0.720 stress. Adaptive execution is faster in mean latency 4/4 seeds; paired median mean reduction 31.37%, paired median p50 reduction 38.51%.

Promotion is blocked by two frozen gates: seed9061701 stress premature executable5/4096=0.1221% exceeds <=0.10%; seed9061702 adaptive p950.659ms vs full0.551ms is +19.76%, exceeding <=10% tail-regression gate. No ordinary premature executable and no premature external YIELD occurred. Do not threshold-tune this allocation.

Interpretation: direct TTC supervision succeeds at learned adaptive compute and median/mean speed, unlike #889's soft compute penalty, but the current confidence-only early-action gate is not yet robust enough under shifted evidence and framework tail jitter. This is HOLD, not PASS.
