# Fresh OpenTTD target/guard continuation

This study transfers the placement-specific target/guard condition from archived
OpenTTD frames and fresh Inkscape integration into fresh OpenTTD processes with
the independent engine scorer. It uses no model calls. Pointer paths, target
boxes, guard boxes and thresholds are authored by the experiment.

## Retained driver failure

The first preregistered pair fails its primary endpoint. Both the wrong-row and
target allocations return `target_not_reached`, stop before B-to-C and fail the
independent score. The target samples contain only 12 changed target pixels;
the wrong-row samples contain 17. All guard counts are zero.

The audit identifies a driver-boundary omission. The program selects the first
road direction at `(709,91)` without first opening Road Construction at
`(820,51)`. Neither allocation constructs A-to-B. This run therefore tests safe
stopping after missing actuation, but does not test the condition after a valid
road effect. Both processes exit normally, all terminals release input, the
save remains unchanged and all 54 `.ait` frames reconstruct their PNGs exactly.
The failed pair remains frozen in `results/openttd-target-guard-live-01`.

## One-click correction

The second study changes one input only: it prepends
`pointer_click(820,51)` before the unchanged direction selection. Seed 991003,
Ctrl+2 pre-action, drags, settle, condition boxes, pixel threshold 24, minimum
target count 120, maximum guard count 20, two-sample requirement, allocation
order and scorer remain fixed.

| Allocation | Condition samples | Later B-to-C | Independent score | Submit to return | First drag to condition |
| --- | --- | --- | --- | ---: | ---: |
| wrong-row | target 17/17, guard 0/0; `target_not_reached` | stopped | false | 3003.541 ms | 2509.126 ms |
| target | target 170/170, guard 0/0; `met` | started | true, all four gates | 4175.154 ms | 2514.704 ms |

The unmet condition reaches the released terminal 8.967 ms after its outcome.
The met condition continues through the second direction selection, drag and
observation, reaching the terminal 1162.248 ms after its outcome. Both cases use
six durable caller operations. All 60 exact frames, releases, process cleanup,
save integrity and engine records audit on Windows and WSL.

## Reverse-order replication

A separately preregistered replication reuses the corrected runner and reverses
the order to target then wrong-row. It reproduces the exact classifications and
pixel counts. The target independently completes the L; wrong-row stops before
B-to-C and remains a negative score. Submit-to-return times are 4129.100 and
3020.568 ms. First-drag-to-condition times are 2526.920 and 2532.837 ms. All 59
frames and lifecycle checks audit on Windows and WSL.

Across the corrected studies, two opposite-order pairs produce four of four
expected condition/continuation/engine outcomes and 119 exact frames. The local
condition removes a model boundary between the first and second road segments
in this scripted task. The roughly 2.5-second first-drag-to-condition interval
includes bounded settling and repeated full observation capture; it is not a
human-tempo result.

Promote this only as a same-seed scripted OpenTTD local-continuation candidate.
The next evidence must change geometry and derive or model-author boxes without
using the independent scorer as planner input. These results contain no model
latency, token, cost, generalization or human comparison evidence.

## Reproduction

From `research/live_control` under WSL:

```bash
python3 audit_openttd_target_guard_live_v1.py
python3 audit_openttd_target_guard_live_v2.py
python3 audit_openttd_target_guard_live_v3.py
```

The original preregistrations, exact transports, PNGs, durable journals, runtime
events, engine observations, cleanup records, reports and audits are stored in:

- `results/openttd-target-guard-live-01`
- `results/openttd-target-guard-live-02`
- `results/openttd-target-guard-live-03`
