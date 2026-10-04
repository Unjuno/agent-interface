# V39 per-key admission to step acknowledgement reconstruction

This is a posthoc, exploratory raw-stream reconstruction of the retained v39 MAP01 trace. It is not a preregistered live experiment and ran no game, model, GUI, OS input, or container workload. The pinned source is `events.jsonl` at commit `c99d93a2c81945f0946173e48247bdd49e32a02a`, SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.

## Result

The raw stream contains 39 per-key `input_admission` rows and 28 aggregate `keys_held` rows. Scoping each admission to the latest preceding active hold `step_started`, then requiring a later same-program/same-step aggregate receipt containing that key with a nondecreasing acknowledgement timestamp, yields:

- 38 admissions associated with exactly one same-step aggregate receipt;
- one unmatched `Down` admission in `cover-4`, step 10, which is followed by a matched cancellation and canceled terminal without an aggregate `keys_held` receipt;
- zero admissions with multiple same-step receipts.

For the 38 associated rows, the interval from per-key `input_ack_ns` to the same-step aggregate receipt's `input_ack_ns` ranges from 8.853 to 38.472 ms, with median 12.771 ms. This is a software-log timing difference between two distinct receipt layers. One aggregate receipt may represent multiple keys, so it is not a per-key acknowledgement clock.

This refines the intentionally broad A04 heuristic in draft PR #7671: later event order plus key membership alone produces ambiguous candidates, while adding same-step context yields a scoped association on this one serialized trace. It does not establish a runtime-authored foreign key or guarantee that the inference transfers to overlapping/concurrent programs.

## H / T / D / C / U

- **H:** One retained v39 trace has per-key admission records without explicit program/step identifiers, plus aggregate per-step `keys_held` records.
- **T:** Read the exact hash-pinned stream from the frozen commit; reconstruct active hold-step scope from ordered `step_started`, `step_completed`, cancellation, and terminal records; require same key, same id/step, later receipt, and monotonic acknowledgement time; independently reimplement with a raw-stream state machine. Five synthetic boundary tests cover grouped admissions, canceled steps, duplicate receipts, stale contexts, and receipts after cancellation.
- **D:** Descriptive result: 38/39 admissions associate with one same-step aggregate receipt; the known cancellation-racing Down admission has none. This gate was not preregistered before exploratory counting and is not presented as a formal allocation result.
- **C:** Event serialization and step-start boundaries explain the associations. A future concurrent writer, missing/reordered log row, or runtime event-emission change could invalidate the inferred scope. An aggregate acknowledgement does not show when every individual key became physically held.
- **U:** Exact per-key release/key-up time, physical keyboard state, independent useful feedback onset, causal task effect, bounded recovery benefit, matched-condition performance, and MAP01 success remain unmeasured.

## Reproduction

From the repository root, run:

```text
python research/doom/v39_admission_step_context_a05_20261005/analyze.py
python research/doom/v39_admission_step_context_a05_20261005/audit.py
python -m unittest discover -s research/doom/v39_admission_step_context_a05_20261005 -v
```

The first command writes `RESULT.json`; the second independently reconstructs and writes `AUDIT.json`. The raw input is read with `git show` from the frozen commit and is not modified.
