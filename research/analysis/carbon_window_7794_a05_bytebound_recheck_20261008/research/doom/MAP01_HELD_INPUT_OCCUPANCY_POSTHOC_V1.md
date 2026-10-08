# MAP01 held-input occupancy posthoc v1

Status: **RETAINED PARTIAL CONSTRUCTION — exact duration not identifiable from the current retained schema.**

This work starts from immutable base `bc21199ac1e22ac34decc9fa1a73190e402480ee` and does not make a new model or GUI call. It addresses the r133 request to measure true held-input occupancy without replacing physical input time with either a program envelope or the requested hold duration.

## Result

The retained X11 path records a key-down admission and acknowledgement, but normal key-up calls return no timestamp. Therefore the exact physical held-key duration is not identifiable from the existing event log. The new analyzer fails closed on that limitation and reports an interval instead:

- lower bound: time from the first acknowledged key-down to the latest event that runtime ordering proves occurred while at least one requested key was still held;
- upper bound: time from the earliest admission attempt to the earliest independently verified empty-input release, or to the post-release observation on normal completion;
- exact duration: always marked unknown under this schema.

For a normal completed hold, `session_v4` semantics establish that snapshots inside the hold loop occur before its `finally` key-up, and the final snapshot preceding `step_completed` occurs after that key-up. For an interrupted hold, the analyzer uses later observations as held evidence only when the earliest verified owner release is explicitly attributed to `cancelled` and the observations precede the cancel command receipt. Expiry, focus, surface, and unknown releases remain conservative at the first key-down acknowledgement.

## Retained v39 sample

One exact event subset from `map01-v39-coast-liveness-live-01`, program `plan-3-primary-0-1`, step 0, is embedded as a regression fixture. The source raw event stream is SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381` in the earlier r133 posthoc record.

The step requested `Down + space` for 500 ms. The first key was admitted at `55531922546329 ns` and acknowledged at `55531922893265 ns`; exact frame sequence 115 was captured at `55532110564498 ns` before the cancel command arrived; InputOwner independently verified empty input with cause `cancelled` at `55532149408597 ns`.

The resulting physical any-key occupancy is bounded to **187.671–226.862 ms**, an interval width of **39.191 ms**. This is one cancellation sample, not a distribution, not total v39 held occupancy, and not a correctness or speed claim.

## Verification and analyzer benchmark

`python3 -m py_compile` passes for the analyzer, its tests, and its benchmark. The synthetic plus retained-sample regression set passes **7/7** checks, including a negative case where a cancelled terminal follows an earlier `focus_changed` release; that case must not treat the pre-cancel observation as proof of continued input.

A container-only compute microbenchmark processed 2,000 synthetic hold steps / 16,000 events for 25 measured repetitions after 3 warmups. Environment: Python 3.13.5, Linux 6.18.44 x86_64, AMD EPYC 9V74, process CPU affinity 5. Median analyzer time was **14.241 ms**, range **12.025–67.963 ms**, corresponding to a descriptive median of about **140,442 hold steps/s**. This measures posthoc analyzer compute only; it is not runtime latency, control throughput, model latency, or gameplay performance.

## H / T / D / C / U

**H — falsifiable hypothesis.** Retained runtime events are sufficient to recover exact physical held-input duration for v39 without a new live run.

**T — minimum test.** Reconstruct normal completion, explicit cancellation, asynchronous release, a cancellation-after-focus-release counterexample, model-wait intersection, admission mismatch, and one exact retained v39 cancellation sample.

**D — disposition.** **FAIL for exact duration; PASS for interval-censored occupancy construction.** Exact duration is rejected because normal key-up timestamps are absent. The interval method passes only if every lower-bound event is ordered before a verified release and ambiguous causes reduce rather than expand the lower bound.

**C — failure mode / competing explanation.** Treating `step_completed`, programmed duration, or a later cancelled terminal as the physical key-up clock would create false precision. An independent focus/expiry release can occur before a later cancel path.

**U — uncertainty.** Dominant uncertainty is unobserved normal key-up time. The reported interval width is therefore structural censoring, not sampling noise. A future runtime version can eliminate it by emitting a lease-bound verified key-up/release transition at the owner boundary.

## Limits and next gate

The working container had no external DNS for GitHub, so the complete repository and full retained v38/v39 raw logs could not be cloned into it. The construction was verified locally from standalone code plus the exact retained sample obtained from the fixed GitHub state. This limitation is retained rather than hidden.

Next, run this analyzer against the complete retained v38/v39 logs in a repo-backed container. If the occupancy intervals are narrow enough, retain the full per-decision and aggregate bounds. If the censoring is too wide for the intended metric, do not infer exact durations: version the runtime to emit physical key-up/release timestamps, freeze that instrumentation, and only then allocate a new matched live experiment.
