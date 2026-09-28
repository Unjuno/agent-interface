# Using the current interface

The current Linux/X11 interface supports explicit actions, referenced images and
bounded continuation. It remains a research preview. The primary model chooses
the action; these entry points do not require a second model or a subagent.

## Choose an entry point

| Entry point | Use | Lifecycle |
|---|---|---|
| [Public CLI/API](cli_v1/README.md) | Existing target mappings and admitted programs; ordinary application integration | One-shot dispatch/observation |
| [Public MCP transport](cli_v1/MCP.md) | The same explicit targets/programs through an MCP host, with native image blocks | Default one-shot; optional persistent/guarded X11; no managed allocation |
| [Scoped public X11 MCP](cli_v1/MCP.md#opt-in-scoped-x11-mode) | Shared image-grounded aliases and input-result images through the public MCP server | Opt-in guarded-x11; one explicit target and retained connection |
| [Native MCP adapter](../research/live_control/NATIVE_MCP.md) | Existing private native harness, or one explicitly managed allocation | Bound run, explicit stages and exact-request resume |
| [Scoped X11 Python API](guarded_x11_v1/README.md) | Explicit image-grounded aliases and guarded input, also included in the portable archive | One caller-owned connection; explicit close and re-grounding |
| [Local integration checks](integration_checks/README.md) | Verify the implementation without GUI or model calls | Fresh output directory with logs |

A persistent Node-capable host can use the [reusable native relay client](../research/live_control/NATIVE_RELAY_CLIENT.md) to retain requests/replies and present text plus images in one response. Its same-request wait is not an input retry. [Primary two-app use](results/native-primary-twoapp-client-01/README.md) records actual saved effects and remaining observation handoffs, with host timing limits and unavailable token accounting made explicit.
An MCP host must launch the configured stdio server and forward its image blocks.
Adding configuration does not prove tools are available in a running host. The
public CLI emits JSON; an assistant integration must render its image payload.
Neither route establishes end-to-end latency merely by returning an image.

## Public actions and images

From the repository root, inspect the installed command surface:

```sh
python3 -m runtime.cli_v1 --help
python3 -m runtime.cli_v1 observe --help
python3 -m runtime.cli_v1 dispatch --help
```

For X11 `observe` or `dispatch`, add `--capture-directory` and `--review` to return
a review envelope in the same invocation. Supply your actual target mapping and
program using the public CLI guide. For dispatch, the envelope selects the last
recorded capture in execution order; operations after it may have changed the
screen. A failed or missing latest capture does not fall back to an earlier one.
A valid image is not proof that an action or task succeeded: inspect the outcome,
execution error and cleanup information alongside it.

For an already saved report, review is read-only:

```sh
python3 -m runtime.cli_v1 review --report /absolute/run/report.json --run-directory /absolute/run
```

Add `--compact` to this read-only command to replace duplicate event objects with
local references. It also accepts `--report -` for a complete response on stdin.
The image, outcome summary and source digest are preserved. Consumers can use
`runtime.cli_v1.receipt_references.expand_receipt` to reconstruct the original
receipt view; only the explicitly listed reference paths are interpreted.
The reviewer selects references only when their serialized JSON is smaller;
otherwise it keeps the original view. The expansion helper accepts either form.
This byte-size comparison is not a measurement of model tokens or cost.
The default representation is unchanged.

For an immediate response, `observe` and `dispatch` accept `--review --compact`
together with `--capture-directory`. This projects the same operation's result;
there is no second observation, dispatch or file-review command. `--compact`
without `--review` is rejected before reading requests or calling a backend.

The report and referenced image must be present at their recorded paths. The
review operation does not recapture, focus a window or repeat an action. Native
research reports use `agent_review.py --native` as described in the MCP guide.

## Retrieve an outcome or request a fresh image

Public MCP offers `interface_dispatch`, `interface_observe`, `interface_results`,
and optional draft checking with `interface_validate`. Validation performs no
input and does not establish runtime admission. For action feedback, choose the
next call according to what is missing:

| Situation | Next call | Meaning |
|---|---|---|
| An action response arrived, but you need its outcome again | `interface_results(call_id="...", include_image=false)` using the returned `call_id` | Reads the retained receipt without delivering its image block or issuing input |
| The action response was lost | `interface_results()`, then look up a candidate ID and compare its retained arguments | Finds calls in this server process; a match still needs caller interpretation |
| The action image is old and you need the current screen | `interface_observe(...)` with the actual target, frame and region | Takes a new read-only capture; it does not repeat the action |
| You want the original image again | `interface_results(call_id="...")` | Returns the retained image, not a new capture |

Listings return the newest 20 calls. Use `next_before_call_id` as
`before_call_id` to inspect older pages. A running call returns `pending`;
`finished` means the worker ended, not that the task succeeded. Missing reports
and unknown IDs remain explicit errors. Do not resend uncertain input to recover
a receipt. The registry lasts only for the current server process.

Image delivery and image availability are separate: `include_image=false` leaves
`image_status`, the image reference and action outcome available, and still
validates the retained image. It does not establish token or latency savings.
See [MCP result retrieval](cli_v1/MCP.md#recover-a-retained-result-without-resending-input)
for the complete lifecycle and failure contract.

## Batch actions between decisions

Use one public `dispatch` program for a finite sequence whose actions can all be
chosen from the current observation. Operations execute in the supplied order;
the model reviews the returned outcome before choosing another program.
For example, after identifying and focusing an editable field, an operation
fragment can move left three characters, insert text, save, capture, and release:

```json
[
  {"op":"key_chord","keys":["Left"],"repeat":3},
  {"op":"text","text":"-"},
  {"op":"key_chord","keys":["CTRL","S"]},
  {"op":"observe","frame":"window_client","x":0,"y":0,"w":400,"h":180},
  {"op":"release_all"}
]
```

This is an `ops` fragment, not a complete executable program. Supply the actual
focused target, observed region, source/binding values and current lease using
[the public program contract](cli_v1/README.md). The example region and shortcut
must match the selected application. Public CLI, API and MCP dispatch share the
same bounded key-repeat compiler: this five-instruction fragment expands to seven
operations, and the complete program must fit 128 operations.

For applications where the caller deliberately chooses paced typing, a text
operation may specify `{"op":"text","text":"300","gap_ms":20}`. This expands
to three character operations and two 20-ms waits, with no leading or trailing
wait. The interval is an integer from 0 to 1000 ms; it is optional, and no
application-independent optimal interval has been established. Expanded text,
key repetitions and all other operations together must fit the 128-operation
limit. Waits consume the caller's lease. See the
[public text pacing contract](cli_v1/README.md) for validation and source mapping.

[Calc pacing follow-ups](results/calc-text-pacing-01/README.md) reproduced repeated-digit
loss through public dispatch despite completed receipts. In one held-out eight-string
sample, explicit 1, 2 and 10-ms gaps each saved all values correctly; zero gaps saved
four. A caller can try a small explicit gap under comparable conditions and verify
the resulting text. This is not a universal default or an application-readiness
barrier, and uncertain input should not be blindly repeated.

Split a sequence when the next action depends on a new image: submit the first
program, inspect its result, then choose the next. An `observe` inside a program
records an image; it does not suspend the remaining operations for model judgment.
A fixed wait also does not acknowledge application redraw or successful saving.
Inspect the action outcome and image separately, requesting a fresh read-only
observation when needed without repeating uncertain input.

The public transport does not offer a durable queue, stack, priority scheduler or
parallel cursors. An overlapping MCP request returns `busy` without executing;
it is not an accepted queued action. Scheduling proposals such as
[#2868](https://github.com/Unjuno/agent-interface/issues/2868) and transport routing
[#3544](https://github.com/Unjuno/agent-interface/issues/3544) remain separate from
this explicit ordered batch. Batching expresses several operations in one call;
its effect on actual model tokens, useful-feedback latency and task correctness
still requires a matched measurement.

## Native decision loop

To reread an exact native result without receiving its image again, call
`native_resume(stage=..., decision_sha256=..., include_image=false)`.
Image integrity is still checked, and outcome, continuation and image reference
remain available. A valid withheld image is marked `image_delivery: omitted_by_request`.
The default remains image delivery; this option is for outcome retrieval, not
a fresh observation or permission to choose input without visual grounding.


Native MCP checks explicitly supplied text gaps, key repetitions and their
expanded tail capacity before publishing a stage request. Invalid compact
syntax returns a tool validation error; the owner receives no request from
that call. Valid requests keep their original compact representation.
When text-policy.json records the harness pacing, submission also checks tail
capacity after applying that default, while preserving the original request.
Explicit per-operation gaps (including zero) still override the default. An invalid
recorded policy rejects new input; observation, finish and exact-request resume
remain available. Historical runs without a policy retain explicit-syntax checks
only. The record is configuration evidence, not an atomic runtime guarantee;
ordinary source, target, capability and lease checks still apply at execution.
A passed syntax check is not admission.

Initial native context includes the recorded `text_policy` when available.
Its `value.gap_ms` is the harness default for text operations that omit
`gap_ms`; an explicit per-operation value, including zero, takes precedence.
The recorded harness defaults are 0, 2 or 10 ms, while explicit operation gaps
accept 0..1000 ms. Missing records return `unavailable`; invalid records return
`needs_review` without an invented default. The source path and byte hash are
retained. This is historical configuration context, not runtime admission,
application readiness or an optimal-typing-speed recommendation.

Native MCP image responses include `window_inventory` when a stage's recorded
listing is available. Read its complete application/dialog titles alongside the
image for exact-title feedback; no separate shell discovery is needed. The
listing is historical and grants no input authority. Missing or malformed
context stays explicit, and ordinary guards still decide admission. See the
[two-app saved-file validation and retained first failure](results/native-window-context-01/README.md).

A native Calc/Inkscape window-review failure can return
`continuation.status: "observation_required"`. Its image is the previous retained
capture, not a view of the state after the action. Use the returned stage and
source sequence to submit only `interaction: "observe"`, or explicitly finish.
Further input is rejected before request publication until that review succeeds.
The completed input receipt remains available; do not resend it. Each explicit
observation consumes a stage, and exhausting the bound still stops the session.
An action's `finish_after` is not applied when its window review fails. See the
[failed baseline and successful live recovery](results/native-review-recovery-01/README.md).

For the six-task primary-use runner, add `--primary-review` to either
`--route persistent` or `--route direct` to pause after each successful local
feedback result. View the printed image and retained task receipt, then
atomically publish the requested JSON file with `task_id`, `source_sequence`,
`outcome` (`complete`, `uncertain`, or `failed`) and a nonempty `reason`.
Only an exact matching `complete` review advances. Other outcomes, malformed
reviews and the 300-second timeout stop; they do not replay input. Primary
interpretation is retained separately from independent task scoring. Timing
includes tool and review waits, not just model inference. See the
[retained six-task primary review](results/native-primary-review-01/README.md).

Result and repair notices include `receipt_summary` next to the image path and
`receipt_file` for full details. The summary preserves operation failures,
recovery state and recorded releases; it does not turn title feedback into task
success. A host can render the referenced image with this notice in one response
before asking the primary model for its next decision. Consult the full receipt
when guard, capture or wait details are needed. See the
[actual combined-notice use and timing limits](results/native-review-notice-01/README.md).

1. Start one explicitly managed allocation, or attach to an existing run. Read
   its goal and initial image using `native_observe(stage=1)`.
2. Choose a decision from that image and submit its exact `source_sequence`.
   Click/keyboard actions need their observed point and expected title.
3. If the result is pending, retain the stage and `decision_sha256`; call
   `native_resume` with those same values. Do not submit the action again.
4. Inspect the returned image and action outcome. `continuation.source_available`
   supplies the next stage/source only when retained source and image identity
   agree. It is descriptive, not permission to skip normal admission checks.
5. To inspect a freshly painted screen, submit only `source_sequence` and
   `interaction: "observe"`. This consumes a stage and sends no input.
   `native_observe(stage)` instead reads an already retained source.
6. Finish with only `source_sequence` and `finish: true`, or explicitly use
   `finish_after: true` on an action when no further decision is needed.

A typed target refusal can return a new image while stage capacity remains. Read
`target_refusal` and choose a new decision; the refused action is not replayed.
At capacity exhaustion, the terminal `needs_review` reply retains the final
observation and cleanup result, and publishes no unusable next source. Process
exit, action completion, cleanup and task evaluation are separate facts.

When recorded verification flags exist, `outcome_summary.cleanup_verification`
projects `tracked_processes_terminal`, `owner_exit_verified` and
`descendants_verified` separately. A `cleanup_status` of `completed` only says the
cleanup routine completed; it does not establish that every descendant exited.
Only explicit booleans are projected; missing or malformed flags are `null`.
The original cleanup receipt is preserved. The managed `allocation` object is a
process snapshot: its `task_success: null` does not override a recorded
`evaluation_success: true`, and a zero process exit code does not prove task success.

For managed research sessions explicitly started with `--owner-lifetime`,
`native_stop()` requests cooperative shutdown without closing the MCP connection.
`stopping` is not terminal or cleanup success: poll `native_status`, and use
`native_resume` only for an exact previously committed request. New input is
refused after stop is requested. This is not immediate interruption; an in-progress
operation can continue until a checked boundary. The default mode is unchanged.
See [the lifecycle contract and retained idle cases](../research/live_control/NATIVE_MCP.md#explicit-cooperative-stop).

## Validate an integration

Follow [the shared check instructions](integration_checks/README.md) for a single
Python environment or split WSL environments. Use a fresh output directory:

```sh
python3 runtime/integration_checks/native.py --output results-local/native-check-01
```

The report includes suite exit codes and hashes of complete logs. The Native MCP
workflow uses this same runner. Broker/bridge contracts have a separate check:

```sh
python3 -m unittest runtime.test_host_model_ipc_broker_v1 runtime.test_docker_host_model_bridge_v1
```

These checks do not start an application or model. Passing them does not establish
human-tempo operation, cross-application reliability, token/cost reduction or
current-model compatibility. Frozen experiments remain evidence for their pinned
sources; integration commits do not extend those claims to a newer build.

### Choose a visually matchable point

Native click and keyboard context checks match a local image patch around the
specified point. A uniform fill can be refused even when a human recognizes the
whole object. For clicks, choose a point inside the intended clickable target
with a visible border or text nearby; choosing another control changes the action.
For keyboard input, the point is a context anchor, not a click destination.

If a response reports `visually_flat_source_region` and `input_dispatched=false`,
inspect the returned image and explicitly choose a new point with its new source
sequence. A refused action is not automatically replayed. See the
[mixed Calc/Inkscape primary run](results/public-owned-mixed-live-01/README.md):
a center-point refusal added one round trip before an edge-point correction.
This observation motivates guidance; it does not measure the guidance's benefit.

When an input field has focus, avoid a patch containing its blinking caret or
text that the planned action will change. A stable border inside the intended
target may preserve context better. This is guidance for the primary model,
not automatic point selection. The [six-task construction pair](results/stable-anchor-six-pair-01/README.md)
retains both correctness and the tradeoff: fewer grounding requests, but more
internal captures and slower local application-feedback handling.

Capture-stage timing is available in X11 image artifacts; see [interval definitions](backends/x11_v1/CAPTURE_TIMING.md). Treat these as local processing measurements, not model-visible completion. The [primary-operated Calc PNG comparison](results/calc-png-integration-01/README.md) retained a faster first response but a slower second response and different final visual readiness with level1 compression. Standard compression remains unchanged; lower encoder time alone is not an adoption criterion.

For native research sessions, `native_observe(stage=...)` reads an already retained frame. To inspect a new state without repeating input, use `native_submit` at the returned continuation stage with a decision containing only the viewed `source_sequence` and `interaction: "observe"`. This consumes one stage and returns a new source to inspect; it does not assert completion. `finish` ends the session and invokes independent evaluation, so use the fresh observation first when another visual check is needed. Count that extra roundtrip in task cost. [Primary-operated example and limitations](results/fresh-observe-calc-live-01/README.md).

### Optional persistent public MCP on X11

For direct public-MCP use, `python -m runtime.cli_v1.mcp_server --targets targets.json --output-directory runs --display :N --session-mode persistent-x11` retains one connection through explicit close or normal transport shutdown. The default is still one-shot. Use the returned `session.binding_revision` (initially 1) in dispatch assertions. `interface_observe` captures a fresh image; `interface_results` reads a retained result without input or recapture.

When a separate dialog owns focus, inspect it with `interface_inspect_target(target)`, then explicitly select the observed native ID with `interface_review_target(target, window_id, review_id)`. The review rechecks the focused client's metadata and its configured transient family, sends no input, and advances the binding revision. Capture the selected surface before sending a new program. A review is not a lease or proof of visual freshness. `interface_close` retains cleanup evidence and never reopens the session.

This opt-in route has one successful primary-operated Calc save following a retained failed save; it does not inherit the research bridge's visual guards or establish generic modal recovery or lower latency. See [contract and limits](cli_v1/PERSISTENT_MCP.md) and [both primary trials](results/public-owned-mcp-01/README.md).
For a dialog whose pixels and target information are both needed, call `interface_inspect_target(target="app", screen_region=[0,0,1280,800])` with the actual screen bounds. This returns one fresh image and target metadata in the same response without selecting the target. Capture failure or changed metadata yields no review ID. Explicit target review still follows; the 30-second review deadline and later observation requirement are unchanged.

Before replacing a field, inspect that the intended text is selected; before Save/Submit, inspect the resulting value when an incorrect value would matter. A batch of click, Ctrl+A, text and Save can finish at the input layer while saving the wrong value. In a primary Inkscape Save-As trial, this saved `shape.svgsaved-copy.svg`; a subsequent trial that reviewed the full-name selection and the resulting `saved-copy.svg` before Save succeeded. This is one observed failure and one follow-up success, not a generic text-replacement guard or a proven speed improvement. All outcomes are retained in [the Inkscape trials](results/target-review-image-01/README.md).
On X11, `focus` preserves the current native focus when it is already the registered client or one of its X11 descendants (including GTK InputOnly children). This avoids resetting an existing input widget to the top-level client. A separate transient dialog is not a descendant: select it explicitly through the existing target review workflow. If focus is outside the target, the backend still requests focus and verifies the resulting ancestry. Verification is momentary; the application can move focus afterward. It is not a modal lock or an acknowledgement that a field processed input. [Native focus comparison and primary save](results/x11-child-focus-01/README.md).
### Capture after explicit target review

Persistent MCP interface_review_target accepts optional screen_region=[x,y,width,height]. It captures after committing the selected target and reports capture_consistency from a subsequent metadata read. Review the delivered image and require appropriate current evidence before input. Matching metadata does not acknowledge redraw or application completion. Without this option, capture separately as before.

Selection and image delivery have separate outcomes: target_reviewed and the new binding_revision remain valid reports of the selection even if capture fails or metadata changes. Do not replay the consumed review token or assume rollback. Inspect again when evidence is unavailable or changed. Retained interface_results does not select or capture again.

## Existing native method reuse

The [native guarded form method](../research/live_control/NATIVE_GUARDED_FORM.md) is now an importable function used by the existing six-task harness. [Primary use](results/native-method-primary-01/README.md) retains six exact submissions, changed-layout refusal and explicit repair. It remains a scoped native integration component; it is not a new public MCP tool or generic semantic form verifier.
