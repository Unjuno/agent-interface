# Held-input telemetry source closure v1

## Scope

Task: `O3-G1-MEASUREMENT-TELEMETRY-001`

Immutable code/evidence base: `bc21199ac1e22ac34decc9fa1a73190e402480ee`

Retained allocation examined: `map01-v39-coast-liveness-live-01`

This is an offline source/trace reconstruction. It makes no new model call, GUI action, OS input, endpoint preflight or formal allocation. Existing raw results and preregistrations are unchanged.

A container checkout was attempted first and failed at DNS resolution (`Could not resolve host: github.com`). That infrastructure failure is retained separately from the scientific result. The numerical reconstruction below was then recomputed in the container from SHA-bound timestamps retrieved through GitHub MCP.

## Question

The r133 control-tempo analysis measures accepted program envelopes during model waits. It deliberately does not establish actual held-key occupancy. This follow-up asks a narrower question:

> What does the retained v39 source and trace actually identify about the interval during which the InputOwner commanded keys to remain down?

This distinction matters because a submitted `hold(duration_ms=...)` is not itself evidence that physical input was held for exactly that duration.

## Source closure

The retained v39 session binds the DOOM backend to `InputOwner` v10. The relevant source path has three important properties.

1. **Key-down is timestamped.** `input_owner_v10.py` records `admitted_ns` immediately before XTest key press and `input_ack_ns` after `d.sync()`.
2. **Ordinary key-up is not timestamped.** The owner issues XTest key release, calls `d.sync()`, removes the key from its owned set, and returns `None`. `session_v5.py` emits only the non-`None` key-down record.
3. **The requested duration is not an owner-side release deadline.** In the inherited `session_v4.py` hold path, synchronous `snapshot()` work occurs inside the hold loop. Ordinary key-up happens only in the `finally` block after the loop exits, and one more snapshot occurs after release. Thus capture/encode/artifact latency can extend a requested hold before the key-up is even issued.

The independent cancellation path is stronger: v10's aggregate `owner_release` releases all owned input, synchronizes X11, queries keymap/button state, and records a `verified_ns` timestamp. It therefore proves an empty-input boundary for cancellation/release, but it does not supply the missing per-key ordinary key-up edge.

## Reconstruction rule

For an ordinary completed hold in this exact retained source lineage:

- the maximum key-down `input_ack_ns` is the time by which the full requested key set has been acknowledged by the owner after X11 synchronization;
- the last **in-hold** observation's `artifact_ready_ns` is a conservative lower bound on ordinary key-up issue time, because that synchronous snapshot must return before the `finally` release executes;
- the final **post-release** observation's `capture_ns` is an upper bound on completion of ordinary key-up plus X11 synchronization, because that capture starts only after the release calls return.

Therefore each ordinary completed hold has a source-bound interval for the owner's commanded key-down lifetime. This is **not** continuous `query_keymap()` measurement: an unrecorded external actor could theoretically release a key early.

## Retained v39 samples

The first two repeated motor cycles of `cover-4` were selected structurally before inspecting their timing result. They contain six completed hold steps.

| Step | Keys | Requested | Owner-commanded full-keyset interval | Overshoot above requested | Release-edge bound width |
|---:|---|---:|---:|---:|---:|
| 0 | `d` | 350 ms | 445.346–463.319 ms | +95.346–113.319 ms | 17.973 ms |
| 1 | `a` | 350 ms | 415.278–425.349 ms | +65.278–75.349 ms | 10.070 ms |
| 2 | `Down+space` | 300 ms | 386.665–396.962 ms | +86.665–96.962 ms | 10.297 ms |
| 4 | `d` | 350 ms | 382.459–393.103 ms | +32.459–43.103 ms | 10.643 ms |
| 5 | `a` | 350 ms | 404.576–419.865 ms | +54.576–69.865 ms | 15.289 ms |
| 6 | `Down+space` | 300 ms | 394.279–404.506 ms | +94.279–104.506 ms | 10.227 ms |

Across these six holds, requested time sums to **2,000.000 ms**. The source-bound owner-commanded full-keyset time sums to **2,428.603–2,503.102 ms**, an excess of **428.603–503.102 ms**, or **21.43–25.16%** over the requested total. Median per-step excess is **75.972–86.155 ms**.

These six observations are one retained episode and are not a population latency distribution. They establish a concrete semantic/telemetry mismatch: `duration_ms` is currently a loop-duration request, not an exact or owner-enforced physical release deadline.

## Active revocation decomposition

The retained natural v39 revocation for `plan-3-primary-0-1` supplies a different, verified-empty boundary:

| Boundary | Interval |
|---|---:|
| health-65 frame capture → typed ready | 8.476 ms |
| typed ready → typed event emission | 4.278 ms |
| typed event emission → cancel command received | 12.435 ms |
| cancel command received → `cancel_requested` | 11.156 ms |
| `cancel_requested` → verified empty owner input | 2.500 ms |
| frame capture → verified empty | 38.844 ms |
| typed event emission → verified empty | 26.090 ms |
| verified empty → `input_released` publication | 12.902 ms |
| verified empty → terminal closure | 52.961 ms |

This preserves the earlier r133 result while locating most of the pre-release delay outside the InputOwner's final cancellation-to-empty interval. It remains one reaction sample, not a hard real-time guarantee.

## H / T / D / C / U

### H — falsifiable hypothesis

Retained v39 source plus raw events are sufficient either to reconstruct actual held-input occupancy or to isolate the minimum missing telemetry needed before a recovery-policy experiment.

### T — minimum test

Read the immutable owner/session/executor source and SHA-bound retained event stream. Reconstruct structurally selected completed holds and the one natural active revocation. Allocate zero new live samples.

### D — decision

**Result: PARTIAL / REPAIR_MEASUREMENT_BEFORE_RECOVERY_POLICY.**

PASS for exact physical occupancy would require a timestamped release edge or continuous physical-state evidence. The current trace does not provide that for ordinary key-up. It does, however, prove that requested hold duration cannot be substituted for actual owner-commanded hold duration.

A recovery-policy implementation remains blocked by this measurement gap and by the separate absence of an independently scored first useful task effect.

### C — competing explanations / failure modes

- The observed excess may primarily be synchronous snapshot/artifact work rather than X11 injection latency.
- An external actor could release a key earlier than the owner without continuous keymap telemetry detecting it.
- These six repeated holds are not representative of all machines, workloads or backends.
- Longer motor occupancy is not necessarily useful control; it may be harmful or irrelevant.
- Altering hold scheduling before instrumenting it could change the phenomenon being measured.

### U — uncertainty

Main unresolved uncertainties are ordinary key-up edge timing, continuous physical occupancy, scheduler/logging/capture perturbation, external input, one-machine/one-episode sampling, and independent task-effect attribution. No numerical combined uncertainty or coverage factor is justified from the retained evidence.

## Decision and next candidate

Do **not** implement a bounded recovery policy yet.

The smallest justified next change is a separately versioned **telemetry-only** path that records ordinary key-up/release edges without changing policy semantics. At minimum it should expose:

- key / button identity;
- owner/intent identity;
- release request timestamp;
- post-`d.sync()` acknowledgement timestamp;
- optional physical-state verification at that edge;
- the same clock domain used by down admission and cancellation release evidence.

The first formal use of that instrumentation should measure requested hold, owner-commanded hold, physical occupancy where observable, no-control time and an independently scored useful effect under a matched condition.

A second architectural issue is now visible but remains unimplemented: if `duration_ms` is intended to be a safety deadline rather than a minimum loop duration, release timing must ultimately move closer to the independent InputOwner instead of being delayed by synchronous observation publication. That is a control-semantics change, not telemetry, and requires a separate task/lease after measurement.

## Retention

Machine-readable result: `results/held-input-telemetry-source-closure-v1.json`.

Reusable analyzer: `analyze_held_input_telemetry_v1.py`.

No retained allocation was rerun, rewritten or relabelled. The negative measurement finding is retained because it changes the next experiment: measurement instrumentation precedes recovery-policy work.
