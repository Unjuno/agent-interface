# MAP01 continuation-guard window T2 — result

**Raw diagnostic:** `PASS_RETAINED_WINDOW_DIAGNOSTIC`

**Execution qualification:** retrospective analysis with harness and auditor reruns; not a preregistered or live allocation.

## Result

The hash-pinned v39 report records decision 2's model wait as 6,306,873,822 ns. Its fresh-action source is typed sequence 70 at health 85. Under the recovery predicate tested in the already merged #59 construction package (fresh sequence and observed health no lower than the predicate source), the first typed rejection evidence inside this model wait is sequence 76: health 82, below 85.

Sequence 76 was captured 1,489,961,751 ns after model start, and the typed value was ready 1,500,507,442 ns after start. The typed record's producer-side `emit_ns` is 1,503,225,914 ns after start, leaving 4,803,647,908 ns before the recorded model end. The paired outer observation row separately records `typed_emit_return_ns=55519837846900`, leaving 4,795,436,977 ns after that producer call returned. Neither timestamp records when a recovery monitor processed the event or when physical input would have stopped.

The candidate output and the corrected raw-only independent recomputation agree exactly with the frozen target constants; four synthetic tests pass, including unavailable-health and stale-sequence rejection. The first auditor version recomputed candidate output but omitted an assertion against the frozen target constants. That audit was retained, corrected, and rerun once; this additional auditor invocation is disclosed in `ATTEMPTS.json`. Frozen input hashes match the retained manifest:

- `report.json`: `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`
- `retention-manifest.json`: `8dfbac52c298d865b4484aaa51dc0d821bb0d74f8c5995d3117206a1ed0dbda2`
- `runtime/events.jsonl`: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`

## Protocol deviation and provenance

The first candidate command stopped before reading any source because `REPO` was resolved one directory too high (`FileNotFoundError` for the pinned report). It wrote no raw result and performed no external action. After correcting that path, the candidate was invoked again and produced `results/raw.json`. The first auditor version omitted the frozen-constant assertion, so it was corrected and invoked again; a later output-field clarification caused one final auditor invocation. These are deviations from the frozen no-retry procedure. The numerical result is retained with those qualifications and must not be described as preregistered evidence or a live allocation.

The analysis branch was created from main `e12e4e2939890d735cb1b11df3a8d8b6a1cf4b9a`. Its path is additive and does not modify the original v39 files or the earlier T0/T1 package.

## Interpretation and limits

At most, this trace says a hypothetical recovery guard freshly sourced at sequence 70 / health 85 would have had a health-decrease rejection available during the model wait, with roughly 4.8 seconds of that wait still remaining. The actual v39 decision records `cover_policy=[]`, `cover_policy_source_iteration=null`, and `monitor_mode=unauthored_coast_no_policy`; no such authored recovery was active. This therefore does not show that a recovery action was running, that cancellation would have occurred at either timestamp, or that the model was interrupted.

No inference is made about physical key-up time, exact guard reaction latency, whether recovery would have improved outcomes, threat-relative policy quality, causal benefit, survival, human tempo, or MAP01 completion. No model, game, GUI, input, Docker, GPU, network, or shared allocation was used.
