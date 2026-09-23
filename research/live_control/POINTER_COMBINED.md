# Actual combined response: successful task, failed presentation

Follow-up: [the live reversible caller](POINTER_VIEW_LIVE.md) completes a new
actual-use episode with both result/image responses visible together. It preserves
this truncation failure and does not reinterpret the two runs as a matched pair.

The assistant used the unchanged v9 OpenTTD caller on the known guarded-road
fixture. Initial observation and first program result were emitted together with
their referenced original PNG in one orchestration call each. The second program
completed, but its full report output exceeded the available model context and
was truncated. The assistant recovered by reading the saved terminal/cursor and
viewing the referenced PNG, **without resending the road-building input**.

An explicit finish then passed the independent three-road connectivity/ownership
contract and 42-tile surrounding guard. Both terminals verified input release;
all owned processes exited and the canonical save remained unchanged. The bridge
process returned zero, observed by polling its existing execution handle after
finish. The runtime cleanup artifact independently records process/save cleanup.

`results/pointer-combined-openttd-01` retains raw records, caller reports,
requests/replies, six AIT/PNG frames, independent score snapshots and diagnostics.
`audit_pointer_combined_v1.py` verifies the full 37-record received prefix against
the raw log, every decoded frame, selected-image hashes, the runtime manifest
source hashes, terminal release, cleanup, and recomputed guarded score.
Caller/wrapper source hashes were not captured in a new predeclared plan for this
episode; this is exploratory self-use, not a qualified comparison.

## Timing and limitations

Initial capture to last terminal was **73.128200974 seconds**; initial capture to
independent evaluation was **358.071190726 seconds**. These are originating-runtime
timestamps. The latter retains the interruption, presentation recovery and finish
delay instead of excluding them. Neither interval isolates model inference or
proves human-like performance. Coordinates and fixture were already known.

The failure was a tool/model presentation boundary failure, not a failed road
program or transport timeout. Its occurrence is evidenced by conversation output;
the runtime log alone cannot establish what the model saw. Therefore this run
does not prove reliable combined result/image delivery for every action, nor a
speed improvement over the earlier self-use cohorts.

## Reversible presentation prototype

`pointer_report_view_v1.py REPORT.json` reads an existing report and prints a
`pointer-report-view-v1` envelope. `payload.exchanges` retains all unique requests,
replies and timing fields. Only top-level `last_reply`, `continuation_batch` and
`terminal` values exactly duplicated in those exchanges are moved to explicit
`references` paths. `unpack()` restores the original JSON values. Errors, unknown
fields and nonidentical receipts remain present; the original report stays on
disk. The envelope is presentation data, not the caller's continuation-batch API.
Use the original or unpacked receipt for the next caller invocation.

| Saved call | Original JSON bytes | Reversible view bytes |
|---|---:|---:|
| open-toolbar | 14,629 | 6,306 |
| build-road | 21,723 | 8,753 |

Sizes use identical UTF-8 JSON serialization settings, not pretty-printed file
sizes. The audit round-trips both actual reports and checks three offline error/
nonidentical-receipt cases, including boolean versus integer distinction.
This preserves JSON values, not original whitespace or member ordering.

This is an **offline presentation prototype**, not yet the live caller default.
Unique records can still exceed a model output budget; no hard output-size bound
or universal truncation fix is claimed. Next: exercise this view plus referenced
image in actual use, retain explicit failure/recovery paths, then compare new
counterbalanced episodes with fixed backend and output settings. Actual model
input tokens, costs and model receipt timestamps remain missing.

Run from repository root in the Linux fixture environment:

```sh
python3 research/live_control/audit_pointer_combined_v1.py
python3 research/live_control/pointer_report_view_v1.py research/live_control/results/pointer-combined-openttd-01/road-call/report.json
```
