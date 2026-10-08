# Reversible report presentation in actual OpenTTD use

Follow-up: [actual Inkscape recovery](POINTER_VIEW_RECOVERY.md) retains a stale
historical clock response, an unplanned key-schema rejection and explicit corrected
execution. This extends actual-use evidence without claiming direct sequence-race
qualification or automatic recovery.

The assistant completed a new known guarded-road episode through
`pointer_exchange_view_v1.py`. Both program calls returned the reversible report
and their validated original PNG in the same orchestration response. Neither
response was visibly truncated; no image-only recovery call or input retry was
needed. This is one successful live integration episode, not a reliability rate
or a paired performance result.

The wrapper delegates input and receipt validation unchanged to
`pointer_exchange_v1.run`. It persists the original `report.json` before packing
the display envelope, checks restoration, saves `view.json`, and prints the view.
It does not change the v9 backend, action semantics, admission lease, timeout,
terminal interpretation, or continuation batch. If presentation fails after input,
the saved report is the recovery source; do not rerun the input command.

## Evidence

`results/pointer-view-live-01/plan.json` was written before launching the fixture
and pins seven caller/presentation/transport source files. The runtime manifest
pins the domain entry, scorer, observer and shared backend sources. The audit
checks both manifests, original/view equality and restoration, separately saved
requests/replies, complete contiguous cursor history, six AIT/PNG pixel identities,
selected PNG hashes, and exactly two admitted/completed programs with verified
release. The independent road scorer passes all target, connection, forbidden-row
and surrounding-road/owner conditions. All owned fixture processes exited and the
canonical save was unchanged. The bridge handle was polled to exit zero.

The visible response experience is documented separately in `presentation.json`:
it is an assistant report from the conversation, not an instrumented model receipt
measurement. The machine audit cannot establish what the model saw from runtime
records alone.

| Call | Original JSON bytes | View JSON bytes | Local clock+program exchange time |
|---|---:|---:|---:|
| Open toolbar | 14,637 | 6,310 | 377.598 ms |
| Select direction, build road, observe | 21,705 | 8,748 | 815.000 ms |

The size comparison serializes both objects with identical UTF-8 JSON settings.
It measures text bytes, not model tokens, image tokens or costs. The local interval
starts inside the caller before its clock request and ends on the program reply;
it excludes shell startup, presentation encoding, image loading, model processing
and subsequent decisions. It is not the complete outer tool-call latency.

Initial capture to final program terminal was **44.571228773 seconds**, and initial
capture to independent evaluation was **59.279988505 seconds**. There were four
task orchestration calls (initial observation, two programs, finish) containing six
socket exchanges; the finish orchestration also polled bridge cleanup. No extra
image-only round trip was required in this episode. The known task, learned
coordinates, non-counterbalanced order and different interruption history prevent
treating the difference from the prior 358-second episode as a speedup estimate.

Admission-to-first-emission was 202.216 ms and 181.334 ms for the two programs.
Those are runtime events, **not first useful feedback at the model**: the second
program's first capture follows toolbar selection, before road construction, and
the caller waits for terminal. The model was shown selected sequences 3 and 6.
Model receipt timestamps, actual model tokens/costs and human comparisons remain
unmeasured.

## Remaining work

The live view is a new explicit entry point; frozen callers/cohorts are preserved.
Unique event records can still exceed an output budget. The next study should
exercise failure/reconciliation and another pointer domain, including stale
observations, rather than adopting this single pass as general qualification.
Before claiming latency improvement, predeclare counterbalanced new cases and
fixed output/model settings, retain all recoveries, and obtain the missing model
receipt/accounting measurements where available. Domain coverage and task effect
contracts remain the architecture criteria.

Reproduce the recorded-data audit:

```sh
python3 research/live_control/audit_pointer_view_live_v1.py
```

Use the new caller with the same positional arguments as the original:

```text
python3 research/live_control/pointer_exchange_view_v1.py SOCKET BATCH RUN_DIRECTORY PROGRAM_ID STEPS --out NEW_DIRECTORY
```

Forward the returned envelope and `payload.image`'s referenced original image
together. Use `report.json`'s original continuation batch for the next program;
the envelope itself is not a runtime command or continuation batch.
