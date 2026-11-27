# Archived Calc timing decomposition and condition discrepancy

This is a read-only re-analysis of the same 12 archived attempts at main `f98fa794c262f23c494e8673b3765be1336f6a6e`, not a new run. `profile_saved.py` first runs each archived two-block comparator, then reads each distinct `exchange/response-N.json` once and sums its reported `runner_ns`. It subtracts that sum from the audited task interval per attempt. The archived host script imports a model adapter; the adapter source at the named source snapshot measures `runner_ns` around planner begin/await using host `perf_counter_ns`. This recount does not independently attest the live imported adapter bytes. Task intervals were measured by the container with `monotonic_ns`; the subtraction compares elapsed durations from different clocks, not absolute timestamps, and their rate agreement was not independently measured.

| Workload | Route | Model-runner sum median | Task minus runner median |
|---|---|---:|---:|
| Fixed | direct | 5.023 s | 1.235 s |
| Fixed | compiled | 4.969 s | 1.592 s |
| Fixed | fresh | 8.374 s | 1.285 s |
| Temporary obstruction | direct | 7.695 s | 1.583 s |
| Temporary obstruction | compiled | 8.219 s | 1.931 s |
| Temporary obstruction | fresh | 10.425 s | 1.671 s |

These medians each cover two samples. Within the recorded forward and reverse fixed blocks, compiled's remainder exceeded direct's by approximately 0.339 and 0.375 seconds; in the two obstruction blocks the differences were approximately 0.348 and 0.347 seconds. The remainder is **not CPU time or pure runtime overhead**: it includes all task-interval work outside the reported runner durations, such as capture, request polling, model-session preparation/closure, OCR, guarded execution and scoring. The compiled path in the saved candidate takes `SAFE_YIELD` and then performs a separate OCR-based guarded Save; direct follows a different continuation. These observations motivate timing those stages separately in a fresh matched experiment but do not isolate a cause or prove an optimization.

The six fixed-block archived `conditions.json` files each contain a conflicting `intervention` sentence referring to 641/283 while their `values` and pass condition specify 472/615. Retained runner input literals, the saved-file oracle and the audited FODS values support 472/615 as the executed/scored values. The discrepancy is not proof of the original author's intent and is not silently repaired; its implications for the documented freeze remain unresolved. The six temporary-obstruction condition files use a different intervention description and do not have that specific conflict.

Run with normal Python and Pillow, using a checkout or extracted archive tree containing the four integration blocks:

```text
python research/analysis/calc_three_arm_accounting_r531_20261101/profile_saved.py research/integration
```

`profile.json` preserves per-call durations, task remainders and condition text. Two observations per route, fixed values and geometry, expected-value OCR, scripted Save, different cache/provider conditions and unequal calls preclude general speed, cost or reliability claims. Old observation images and underlying source/receipts remain in the original archives. `-O` is refused because the archived auditors use assertions.
