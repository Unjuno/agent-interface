# Unified runtime CLI/API v1

This is the model/vendor-neutral local entry point over promoted Agent Interface backends.

For a retained `prepared_exchange` action report, inspect the result and latest
observation without printing the full routine event history:

```bash
python -m runtime.cli_v1 receipt --report /path/to/report.json
python -m runtime.cli_v1 receipt --report /path/to/report.json --raw
```

The default view retains every top-level report field, the full latest
observation(s), terminal/evaluation/error events and all unknown event types.
It moves older observations and routine command/admission/step records out of
the view, keeping their counts and the raw report's path/SHA-256. `--raw` returns
the complete parsed report. Use raw history when intermediate states matter.
This is an opt-in historical result view, not a live stream reducer or a new
observation; it neither sends input nor renews a lease. Reading succeeds with
exit code 0 even when the report describes a failed task: inspect its status and
outcome. Malformed receipts return `invalid_receipt` and exit code 2.

An [actual assistant XTerm run](../results/receipt-self-use-01/README.md) records
the motivating truncated output and the subsequent use of this view. Byte counts
there are not model-token or performance measurements.

```bash
python -m runtime.cli_v1 doctor
python -m runtime.cli_v1 dispatch \
  --program program.json \
  --targets targets.json \
  --current-observation-seq 7 \
  --current-binding-revision 3
```

`targets.json` remains explicit native target identity:
- Linux/X11: X11 window IDs;
- Windows: HWNDs;
- macOS: PIDs.

The CLI does not discover targets, rewrite leases/freshness, retry automatically, or grant authority. `doctor` is diagnostic only. `dispatch` delegates to `selector_v1`, then the promoted backend session, then `runtime/core_v1` admission.

Each `dispatch` owns its one-shot session and closes its native backend connection
when that backend exposes `close`, including after refusal or an execution error.
A close failure returns `runtime_failed` with `cleanup_error`, preserving any
execution result or original error. The CLI consequently exits nonzero. This
connection cleanup does not replace the backend's input-release checks.

Wayland-only Linux currently fails closed because no Wayland backend has been promoted. Linux/X11 requires the existing `python-xlib` dependency used by `x11-v1`.


Golden-v3 boundary is provided by runtime.cli_v1.golden_v3.dispatch_golden_v3; it preserves the existing dispatch contract and is authority-neutral.

Its `golden-v3-result-v2` result distinguishes native program completion from
application scoring. Native `completed` sets `program_completed: true`;
`task_success` remains `null` when no independent task result was supplied.
Native refusal retains its error and returns `refused`. Unverified release does
not count as completion. `status: success` requires both completion and an
explicit positive task result, with no dispatch or cleanup failure.

Cleanup failure sets `status: cleanup_failed` and `task_success: false` without
erasing already reported program completion; any supplied application result
is preserved in `raw_dispatch`. Consumers must use `status` for overall
success rather than either boolean alone. `raw_dispatch` retains the complete
dispatch response, including native observations, release evidence and effects,
even when the adapter cannot interpret it. The older `partial_effects` list is
only a forwarded field: an empty list is not proof that no input occurred.
These changes replace v1's conflated success booleans; callers inspecting the
schema must accept v2 explicitly. This adapter still does not perform visual
target revalidation, compile guarded methods or obtain an application score.
