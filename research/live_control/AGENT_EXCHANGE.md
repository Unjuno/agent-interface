# Prepared exchange for the agent's own loop

`agent_exchange.py` composes existing v27 preparation and socket exchange. After
viewing a received image, provide its complete batch and explicit steps in one
Python call, or one JSON object on stdin:

```python
from agent_exchange import run
report = run(socket_path, received_batch, run_directory, "edit-1",
             [{"op": "text", "text": "draft"}],
             out="results-local/edit-1", boundary="terminal")
```

The CLI is `python research/live_control/agent_exchange.py --request -`.
Its JSON keys are the Python argument names (`socket_path`, `batch`,
`run_directory`, `program_id`, `steps`, `out`, and optional `lease_ms`,
`boundary`, `timeout`). `batch` is an object, not a filename. Use a new output
directory for each deliberate action. Defaults: 5-second lease and wait,
terminal boundary. `boundary="outcome"` submits the final program with
`finish_after=true`; explicit session cleanup is still required.

For CLI calls, replace `batch` with `batch_file` to read the explicitly selected
full received batch or prior `report.json`. Supply exactly one source form.
This avoids copying result JSON into the next request or generating steps files:

```json
{"socket_path":"/tmp/SESSION/events.sock","batch_file":"results-local/previous/report.json","run_directory":"results-local/session","program_id":"next-action","steps":[{"op":"observe"}],"out":"results-local/next-action"}
```

Send this object on stdin with `--review`. Relative paths resolve from the client
working directory. The loader reads once; `source-batch.json` retains the full
loaded object. It does not search for a latest file or unwrap a compact receipt
view, which may omit history. The referenced file must contain `cursor` and
`records`. Existing clock, image and runtime admission checks still apply: file
selection alone proves neither viewing nor freshness. A completed final action
does not become eligible for further input simply by referencing its report.
See [actual Inkscape use](../../runtime/results/inkscape-batch-reference-01/README.md)
for a viewed selection followed by a saved position edit using this entry point.

If the outcome is early saved-effect evidence, the adapter now composes the
existing `drain_final` policy: one command-free request for an already-available
independent evaluation, zero server wait, and a 250-ms transport deadline.
No loop or input retry occurs. Pending/lost reads retain early evidence and a
continuation; mismatched identities require reconciliation. Exact final-read
requests/replies and the full drain interpretation are retained. An evaluated
result can therefore arrive with the original action response without another
model/tool turn. If evaluation arrives too late, a later command-free read is
still required. Early effects are never promoted to task success by themselves.

The adapter makes one clock request and at most one submit. It preserves the
reviewed observation/delivery reference, requires a contiguous own-clock reply
without intervening events, then uses the existing preparation logic. A clock
does not refresh the image. Any changed sequence or intervening event requires
review. This deliberately conservative candidate assumes one caller and an idle
session between decisions. It is not a continuous-game control loop.

Exact requests are persisted before transport, replies after receipt, followed
by a complete report. There is no automatic input retry. `program_attempted`
means a potential transport write, not admission or execution. On uncertainty,
inspect saved artifacts and reconcile with command-free reads. A reused output
directory is refused, but a different directory is not a session-wide replay
guard. Persistence failure can leave a partial artifact set; the CLI reports
unknown attempt state in that case.

`boundary` status and CLI exit zero do not mean task success. Inspect terminal
status, release and independent evaluation. For a smaller presentation of the
saved report, use `python -m runtime.cli_v1 receipt --report PATH`; retrieve raw
intermediate observations when they matter to the next decision. The adapter
does not infer actions, run another model, or modify frozen component sources.

Actual assistant use, including the first rejected development attempt, is
retained in [composed self-use](../../runtime/results/composed-self-use-01/README.md).
This is a research integration candidate, not native CLI/backend convergence.

## Return the receipt and image together

Pass `--review` to `agent_exchange.py` to compose the action attempt and its
review in one CLI invocation. The raw report is persisted first. Review failure
returns that action result plus `review_error`; it never repeats input. The CLI
exit status continues to describe the action adapter status, not rendering or
task success. Forward the optional image block as described below.

After `run` has persisted its report, `agent_review.review(report_path,
run_directory)` returns the receipt view plus the exact referenced PNG bytes
as an image content block. It can run immediately after the action in the same
Python process. For an existing report:

```sh
python research/live_control/agent_review.py --report results-local/edit-1/report.json --run-directory results-local/session
```

Forward the `image` block to the host image channel, not to text. For this
tool host, after awaiting the completed CLI command:

```javascript
if (commandResult.session_id || commandResult.exit_code !== 0) {
  text(commandResult); // resume the existing session; do not repeat the action
} else {
  const review = JSON.parse(commandResult.output);
  const frame = review.image;
  delete review.image;
  text(review);
  if (frame) image(frame);
}
```

The output budget must fit the complete JSON plus base64 image. Truncation must
not be repaired by guessing or replaying input: repeat only the read-only review
with an adequate output budget, or use the existing file-image path. Base64 adds
transport bytes; there is no token-saving claim. This path removes host path
mapping and a separate image-read tool call. The host still performs image
rendering. The helper does not decode PNG pixels; it checks the signature and
hash of the exact encoded bytes passed to the renderer.

Newest-reference conflicts, missing images or changed saved image identities
return `image_status="needs_review"` while retaining the receipt. There is no
fallback to the pre-action source image. Full intermediate history remains in
the original report. The image remains a historical capture and may precede
task evaluation; displaying them together does not prove a post-effect capture.

## Request a rendered boundary before the next decision

The selected v27 runtime already inherits `settle` from `session_v8`. When an
explicit GUI action is expected to open or close a dialog, a caller can append:

```json
{"op":"settle","quiet_ms":200,"timeout_ms":1200}
```

This samples pixels and focus until they remain equal for the quiet interval,
or the polling budget expires. Supported quiet interval: 40–250 ms; timeout:
quiet interval through 2000 ms, within the program's combined wait budget.
It emits `settle_result` with reason, sample count and elapsed time. The receipt
keeps this event visible. Captures/encoding may overrun the nominal timeout;
this is not a hard wall-clock deadline.

Use it as the final observation step before returning to the agent. View the
returned image before choosing a dialog response. Quiet pixels neither prove
rendering completeness nor semantic completion, and do not refresh input
authority for a later input step. Animations can consume the timeout; a blank
surface can be quiet. Do not add it indiscriminately to continuous-game input.

[Actual Calc self-use](../../runtime/results/calc-settle-self-use-01/README.md)
received readable dialog and dismissed-dialog frames in two calls, with saved
content independently verified. It avoided a separate observation program in
that example while performing extra native captures. Token and general latency
benefits remain unmeasured; the runtime implementation was unchanged.

## Optional exact event references

Use `agent_exchange.py --review compact` or `agent_review.py --compact` to
replace duplicate complete event objects inside receipt report metadata with
`{"event_ref": N}`. The full object remains at `receipt.events[N]`, in the same
response. Only paths listed in `receipt.event_references` are references; an
identically shaped object elsewhere remains literal data. The v2 schema is
explicit, and `expand_receipt` reconstructs the original v1 receipt view.

This replaces exact copies only. Near-matching, conflicting and unknown events
remain present; all event-list entries and latest observations stay complete.
The original full report and image are unchanged. Earlier history omitted by
the v1 view still requires the raw report; expansion recovers the v1 view, not
that omitted history. Reference lookup requires no additional tool call.

`--review` alone keeps its original full presentation. Compact mode is opt-in:
reference bookkeeping can increase size on receipts without repeated events,
and model interpretation/token/latency effects have not been measured. See the
[same-receipt comparison](../../runtime/results/receipt-event-references-01/README.md).


## Present native bridge observations

The same presenter accepts explicit native observation files or feedback/window
review rows with an `observation` field:

```sh
python3 research/live_control/agent_review.py --native \
  --report results-local/native-review-self-use-01/source-2.json \
  --run-directory results-local/native-review-self-use-01
```

Decode JSON, present the receipt as text, and render the returned `image` block
through the host's image output (do not print base64 as text). Keep adequate tool
output capacity; a truncated JSON response must only be re-read, never replayed
as input. Native review retains the complete native report and exact source hash.
It checks the raw-capture hash link, capture time, PNG digest/signature and path
inside the explicit run directory. It does not decode pixels or authenticate the
producer. The image remains a historical capture; it grants no input authority.

A missing explicit observation returns `no_observation`. Broken references or
identity mismatch return `needs_review` with the receipt preserved. No old image
is substituted. Optional native `--compact` is described below. See the
[actual Calc use](../../runtime/results/native-review-self-use-01/README.md).


## Submit, wait and review the private native harness

Use `agent_exchange.py --native --request request.json` with an explicit object:

```json
{
  "run_directory": "results-local/my-private-run",
  "stage": 1,
  "decision": {"source_sequence": 1, "point": [18, 108], "tail": [],
               "expected_title": "sheet.xlsx — LibreOffice Calc"},
  "timeout": 5
}
```

Use only decisions grounded in the presented source. The existing Calc harness
must already be running with a fresh output directory. This mode publishes one
immutable stage request, waits up to the polling budget (0..30 seconds), then
returns the correlated native report and image via the existing presenter.
A reply is correlated by stage and hash of the exact committed decision bytes.

On `pending`, input may have happened: keep the exact request, add `resume:true`,
and call again to read only. A second submission refuses the occupied slot.
A missing request on resume refuses instead of creating one. Never delete request
slots to retry, reuse run directories, or infer that a timeout means no effect.
The adapter cannot deduplicate across a restarted/mutated server. This is a
private single-owner research transport, not the promoted public API.

The actual [Calc exchange run](../../runtime/results/native-exchange-self-use-01/README.md)
includes normal combined action/image, intentional timeout/read-only resume,
and independent saved-file evaluation. The response is a full native report;
optional compact review is described below. CLI exit alone is not a task-success signal:
inspect pending/error status or the explicit independent evaluation in the report.


## Optional exact native observation references

Use `agent_review --native --compact` or `agent_exchange --native --review compact`
(or native request `compact:true`) to replace exact copies of the top-level
`native_result.observation` with local references. The complete observation stays
in the same receipt. `observation_references` lists the only JSON-pointer paths
that are references; other reference-shaped values remain literal. A compact
receipt declares `agent-interface/native-receipt-v1-observation-refs`.
`expand_native_receipt` reconstructs the full receipt without a tool call.

This compares complete observation objects, including identity and time; different
captures are never merged just because pixels match. Errors and all guard checks
remain. The image itself is unchanged. If reference overhead would not reduce
serialized bytes, the ordinary receipt is returned. Default behavior remains full.
The [fresh Calc run and paired byte comparison](../../runtime/results/native-compact-self-use-01/README.md)
show a modest text reduction; actual model tokens, cost and performance benefits
remain unmeasured.


## Second application: Inkscape

The existing `run_native_calc_self_use_v1.py` keeps its historical filename and
Calc default, and accepts `--app inkscape`. It uses the same immutable stage slots,
agent_exchange --native and image review; output is retained as shape.svg and
scored only after explicit finish. Ground each point on the current presented
image. X11 keysyms are case-sensitive (Right, not RIGHT).

GTK may focus a child of the registered top-level window. The guarded bridge
checks ancestry and preserves that exact focus, rather than changing focus and
invalidating its own handle. A stable child is accepted by read-only review and
title-cue feedback; task effect still needs independent scoring. See the
[retained failures and actual Inkscape use](../../runtime/results/native-inkscape-transfer-01/README.md).
