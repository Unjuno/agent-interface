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

X11 execution errors return nested `status: execution_failed` with the retained
`execution` record. `completed_ops` lists zero-based operations that returned;
`failed_op` identifies the interrupted operation, whose effects remain unknown
and may include partial input. Observations obtained before failure, per-program
emission count and recovery-release results survive. A failed recovery release
is recorded separately from the original execution error. None of these fields
prove application success or authorize replay of the completed prefix.

Wayland-only Linux currently fails closed because no Wayland backend has been promoted. Linux/X11 requires the existing `python-xlib` dependency used by `x11-v1`.

For assistant-visible observations on X11, pass `--capture-directory DIRECTORY`
to `dispatch`, or `capture_directory=...` to the Python dispatch APIs. This
optional path additionally requires Pillow. Each native `observe` encodes a PNG
from its existing GetImage reply and returns its path, PNG SHA-256, dimensions
and source-raw SHA-256 in `artifact`, alongside the unchanged raw pixel hash.
The row also records target/window, frame/region and capture start/end clocks.
The directory is caller-selected; generated filenames are unique and created
without overwrite. No second capture is substituted for that observation.

The initial encoder supports 24-bit TrueColor with 32-bit pixels and the usual
RGB masks, in either byte order. Unsupported formats or encoding/write errors
return `artifact_error` while retaining the captured metadata and execution
result. Consumers needing an image must check that field. Artifact creation is
not an application score or a renewal of observation/input authority. It can
show the state before an asynchronous save has rendered, even if a later scorer
confirms the save. Other backends reject this option before dispatch. Default
hash-only behavior remains available without Pillow.

After an input result, request a new observation without replaying input or
changing focus:

```sh
python -m runtime.cli_v1 observe --targets targets.json --target fixture \
  --frame window_client --region 0 0 400 180 --capture-directory observations
```

The equivalent Python entry point is `runtime.cli_v1.observe.observe`. Currently
this read-only path is implemented for X11. It captures once, closes its own
connection and returns `agent-interface/runtime-observation-v1` with a new
`observation_id`. It never dispatches a program, focuses the window, replays an
action, releases held input, refreshes a lease or supplies task success. A close
failure keeps any captured observation but returns `observation_failed`.
Capture/encoding status must still be checked, including `artifact_error`.
The existing X11 backend constructor requires XTEST even for this read-only
entry point. Regions are bounded to 8192 pixels per dimension and 16 Mi pixels.

This gives callers the continuation primitive for delayed rendering. The caller
still chooses when another observation is useful and whether its pixels prove
the intended effect; repeated observation is not an implicit completion test.


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


Read a retained prepared-exchange receipt together with its referenced PNG:

```sh
python -m runtime.cli_v1 review --report report.json --run-directory /absolute/run
# The portable runtime supports the same command:
python agent-interface-runtime.pyz review --report report.json --run-directory /absolute/run
```

The JSON response contains the receipt view and an image block (`type`,
`mimeType`, base64 `data`) that a host can forward to its model image input.
It selects the newest referenced observation, including terminal review, and
checks path containment, capture identity and PNG signature. It never falls
back to an older frame when the newest image is missing. `image_status` is
`image`, `no_observation`, or `needs_review`. Exit 2 signals an invalid receipt
or unavailable/conflicting image; a valid receipt is retained when its image
cannot be read. Exit 0 means presentation succeeded, not that the task succeeded.
This is historical evidence: no new capture, input, completion inference or
sensor registration occurs. Native research reports use the research adapter;
this command accepts the existing prepared-exchange receipt format.
