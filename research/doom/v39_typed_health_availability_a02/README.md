# v39 typed-health availability timing — A02

## H/T/D/C/U

- **H:** Replacing capture time with typed-observation emit/availability time may shift a two-decrease trigger enough to alter a short-window replay.
- **T:** On the frozen v39 trace, compare capture_ns and outer observation emit_ns using the already preregistered two-consecutive-numeric-decrease rule and W={0.5,1,1.5,2,2.5,3,4}s.
- **D:** 634 event records / 218 typed observations / six waits; raw SHA-256 report `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`; events `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
- **C:** Frozen input and rule; no threshold retuning. 84 clock × wait × window slots.
- **U:** Retrospective single-trace timing sensitivity only; neither intervention utility nor safety is tested.

## Result

Candidate run once. Capture and emit clocks selected the same trigger sequence in all 84 slots (0 changes). Capture-to-emit delay was min 10.571 ms, median 13.342 ms, p95 17.808 ms, max 24.895 ms. Thus emit-time replay changes the reported trigger availability instant by roughly 10–25 ms but did not alter whether/which observation triggered under this trace and grid.

Examples: no-policy d2 at W≥2.0s triggered at seq81 (capture +3193.790 ms; emit +3206.176 ms; 3113.084 vs 3100.698 ms remaining). No-policy d3 at W≥2.5s triggered at seq103 (capture +3405.430 ms; emit +3418.433 ms; 3319.562 vs 3306.559 ms remaining). Authored-policy waits d4 and d5 also trigger, so the signal is not exclusive to unauthored coast. In d3, one row was captured before wait start but emitted after it; it did not change the trigger sequence.

An independent all-pairs implementation matched all 84 clock/wait/window slots with zero mismatches and verified pinned source hashes.

## Preserved failure history

A01's candidate runner had an inline JavaScript syntax error before it fetched or parsed data; it produced no values and is retained in the A01 `runner-stop.json`. This A02 was the single corrected candidate execution. Earlier two-drop A01 JSONL parsing and independent-audit-v1 Web Crypto failures remain unchanged in their original experiment folders; corrected A02 and audit-v2 evidence is retained in the neighboring window experiment.

## Interpretation / stop boundary

This result says that choosing observation availability time instead of capture time adds a small latency and, for this fixed trace and preregistered grid, does not change trigger sequence. It does not demonstrate a functioning online monitor, interrupt effectiveness, false-interrupt rate, saved model cost, correct replanning, admission, safe input, survival, or task completion. Do not treat this as authority to interrupt or control. Further intervention requires a distinct prospective preregistration and authorized allocation.
