# Using the current interface

The current Linux/X11 interface supports explicit actions, referenced images and
bounded continuation. It remains a research preview. The primary model chooses
the action; these entry points do not require a second model or a subagent.

On Windows, use [WSL-native development](WSL_NATIVE.md) for local setup and
contract checks. Docker Desktop is not required for these entry points.

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

For a host that understands v3 receipt references, use the existing explicit
`compact=true, report_refs=true` flags on both `interface_observe` and
`interface_dispatch`. For example, an observation's arguments can be:

```json
{"target":"configured-name","frame":"window_client","region":[0,0,560,260],"compact":true,"report_refs":true}
```

Choose the actual configured target and region. Read the complete report at
`receipt.source.raw_report` in that same response; `receipt.report` may be a local
reference. Native image blocks and outcome summaries remain available. Python
clients can use `runtime.cli_v1.receipt_references.expand_receipt` to restore v1.
These flags are not arguments to recovery or target-management tools. Defaults
remain full for compatibility. A [recount of primary replies](results/public-observation-projection-01/README.md)
found avoidable text duplication in three observations; this measures bytes,
not model tokens or cost.

[Primary Calc use](results/calc-compact-primary-01/README.md) exercised these
flags while entering and saving 336/439 through a format-confirmation dialog.
Saved worksheet values matched. For `screen_physical_px` captures, the recorded
native_window_id identifies the configured target, not necessarily the focused
client shown on screen. After a dialog closes, use target inspection/review before
continuing input on the main window; a screen image does not implicitly rebind it.

[Primary input-recovery use](results/input-recovery-primary-01/README.md)
records a failed press that had already changed a visible counter, explicit
same-session release recovery, visual review and a newly authored continuation
that saved the requested value. This small injected-fault construction exercises
the recovery workflow; it does not measure general reliability or speedup.
An optional target/region on recovery now returns a post-release window image
in the same call. [Fresh primary use](results/recovery-capture-primary-01/README.md)
completed the same construction with six rather than seven MCP calls. Capture
failure preserves the committed recovery result; observe separately if needed.

## Long-lived guarded sessions

Guarded X11 history keeps two decoded full-screen images in memory and reloads
older explicit grounding sources from their exact hash-checked PNG artifacts.
Source sequences, images and fresh guards are unchanged. Missing/corrupt old
artifacts refuse grounding; they are never replaced with a new screenshot.
Metadata, handle patches, disk files and caller-held images still require bounded
session lifetimes. [Retention evidence](results/decoded-observation-history-01/README.md)
includes a scoped primary task and an isolated memory comparison, not a model
latency, token-cost or human-tempo claim.

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

## Python calls on one owned X11 connection

For a serialized Python caller, `MCPSessionOwner.dispatch` shares the persistent
MCP route's dispatch bookkeeping. After establishing the actual target mapping,
selected display and current source, use the same complete public program:

```python
from runtime.cli_v1.mcp_session import MCPSessionOwner

owner = MCPSessionOwner(targets, display_name=selected_display)
try:
    report = owner.dispatch(
        program,
        current_observation_seq=reviewed_sequence,
        current_binding_revision=owner.binding_revision,
        capture_directory=run_images,
    )
finally:
    cleanup = owner.close()
```

The variables above are caller-supplied; this is not a complete allocation or
source-grounding example. The method records the cleanup obligation before
calling the public API, so callers do not need to assign `dispatch_attempted`
manually. It returns the API report unchanged. A mismatched binding revision
refuses dispatch; even that call may initialize the connection. Initialization
failure is consumed once, and a closed owner cannot reopen.

Source values and leases remain explicit. The method adds no inspection,
replay, renewal, task-success inference or implicit input recovery. Review the
input report and cleanup independently; an exception can follow input emission.
`close()` attempts release on that same connection and reports failures. It does
not prove the task succeeded. Use explicit `inspect_after_dispatch` when fresh
post-release target context is wanted. This wrapper applies to its own ordinary
public session; a compiled graph using a separate connection retains its own
input owner and cleanup duty. Calls must be serialized by the caller.

[Fresh primary Inkscape use](results/inkscape-owned-public-01/README.md) used this
entry point for two pointer drags in one program, followed by a visually chosen
save program. The independently inspected SVG met the two-rectangle predicate.
This is scoped transfer evidence; it does not establish a comparative speed or
token benefit.

## Explicit Python summaries of retained dispatch reports

A Python caller can opt into the same success-only summary as CLI/MCP while
keeping an arbitrary original report filename. Review the exact retained bytes,
then supply their path and the directory used to resolve image artifacts:

```python
from pathlib import Path
from runtime.cli_v1.review import review_bytes
from runtime.cli_v1.public_summary import summarize_retained_dispatch

report_path = Path(saved_report_path)
full = review_bytes(report_path.read_bytes(), run_images,
                    compact=True, report_refs=True)
shown = summarize_retained_dispatch(full, report_path, run_images)
```

The caller already retained the report; this reads it and does not write, capture
or dispatch input. The method checks the exact byte length and SHA-256 before
using the existing completed-and-released summary gate. It preserves the original
image, reference, outcome, capture and release evidence. Only supported repeated
program/expansion/wait details are omitted. The partial summary explicitly names
the exact full report and its hash for read-only CLI retrieval without an image.

Missing, changed, unsupported or failed reports keep the full view. The ordinary
file `review()` can return v1 when compaction is not smaller; this helper then
keeps it full. The example uses `review_bytes` to match the existing received-report
presentation shape. It does not make a retained image fresh or acknowledge task
success. Default dispatch and full presentation remain unchanged.

[Two retained Inkscape projections](results/retained-python-summary-01/README.md)
verify byte-identical images/outcomes and exact full retrieval. Text bytes are
measured separately from image payload; no model-token, cost or speed benefit is
inferred from the offline comparison.

[A four-case primary Inkscape comparison](results/inkscape-live-summary-01/README.md)
completed both representations correctly with identical saved results per pair.
It did not meet the predeclared joint token/declaration-time improvement gate;
full remains the default and summary remains an explicit option.

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
In guarded X11 mode, the existing five-second lease includes typing and waits.
Expiry interrupts waits and prevents subsequent key presses, preserving partial
execution and attempting release. The default post-result image still shows the
state after that attempt. Review it before a new explicit action; do not replay
the failed tail. Blocking X11 calls are not preempted, so this is not a hard
real-time guarantee. [Primary expiry evidence](results/guarded-tail-deadline-01/README.md)
records a stopped suffix and an independently correct reviewed continuation.
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

If this persistent session reports `recovery_required=true`, normal dispatch
stays blocked. Explicitly call `interface_recover_input` with its current binding
revision to attempt tracked-input release/readback. Verified empty release clears
only that block and advances the revision; old programs and pending target reviews
become invalid. Observe/review current state before a newly authored program.
Failure keeps recovery required. This never replays a failed action or reconnects.
[Real-MCP boundary evidence](results/explicit-input-recovery-01/README.md) covers
held-input recovery, stale-request refusal and a new program on the same owner;
application effects and task completion remain unproven by recovery.

X11 registers a key/button cleanup obligation before attempting a press, so an
uncertain send/sync failure does not erase the release target. Failed release
readback retains the obligation for explicit recovery. The
[controlled regression](results/x11-uncertain-press-release-01/README.md) preserves
a prior falsely verified release with an independently observed held key, plus
corrected private-X11 and real-MCP boundary checks. Successful-path request counts
are unchanged; server loss can still prevent release and these checks do not
measure exact key-up timing or task effects.

Public dispatch `observe` operations also accept `region: [x,y,width,height]`,
matching `interface_observe`. Use either this form or legacy `x/y/w/h`, never
both. Explicit lowering happens before admission and is retained in the report.
The [primary-use regression record](results/public-observe-region-01/README.md)
preserves the original syntax refusal, successful region-form movement/camera
observations, and a mixed-form request refused before any input.

When using the research `PrivateSession` fixture, app launch now follows an actual
window-manager readiness probe (managed and viewable), not just an X11 handshake.
This affects fixture setup only. The [retained Operations World smoke](../research/live_control/results/private-x11-readiness-01/README.md)
includes the original startup failure, real-X11 controls, primary-operated public
MCP movement/camera input and task-discoverability/authoring questions. It does not establish
task completion or improved interaction latency.

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


### Optional guarded brief responses and strict argument names

In guarded-x11 mode, interface_guarded_input accepts detail="brief" (default "full"). It summarizes only known normal exact-match guard details; all other result fields and images remain unchanged. Critical or unfamiliar evidence stays full. Follow presentation.retrieve to interface_results with detail="full" for retained details; this does not replay input. Full raw reports remain authoritative.

Use interaction="keyboard" for keyboard-only input and provide the minted offset. Unknown top-level tool arguments are now rejected before operation invocation: pointer=false is not supported. Hosts must pass through SDK text errors rather than assuming every text block is JSON.

Primary six-task evidence: runtime/results/guarded-mcp-brief-primary-03, including one unexpected ignored-argument recovery and one planned stale-layout refusal. Previous interrupted and failed trials are retained beside it. The byte reduction is a same-report metadata comparison only, not measured model-token or speed savings.

### Register several explicit references from one image

In guarded-x11 mode, interface_guarded_mint_many accepts one viewed source_sequence
and 1–8 references, each with alias, point and region_size. It uses the existing
single-reference registration rules and returns each alias and offset. This sends
no input and selects no targets for the model. Duplicate aliases and malformed
reference schemas are refused before opening the backend.

Registration is sequential, not atomic. On mint_incomplete, inspect minted,
failed_alias, failed_alias_state and unattempted_aliases. Earlier registrations
remain; the failed alias may already exist if persistence failed. Do not replay
the batch assuming rollback. Retrieve the retained call for evidence.

[Primary six-task use](results/guarded-mint-many-primary-02/README.md) registered
five explicit references in two calls, recovered from the planned stale-layout
refusal, and completed six independently correct submissions exactly once.
[The prior interrupted trial](results/guarded-mint-many-interrupted-01/README.md)
is retained. This establishes scoped usability; matched speed and actual model
token/cost improvements have not been measured.

### Reduce duplicated observation metadata

Set observation_refs=true on guarded observe/input or a retained-result lookup
to opt into local references. When observation_report.observation contains
`{"observation_ref":"/source/native"}`, read the complete metadata at source.native
in the same response. This is the same capture, not a freshness or authority
refresh. The image block is unchanged. Leave the flag false for the prior shape.

The [primary six-task trial](results/guarded-observation-refs-primary-01/README.md)
completed six correct exact-once saves, retained full refusal details, and verified
full retrieval plus referenced image retrieval after close. Actual returned text
was 9.6176% smaller than the same views with references expanded. Actual model
token/cost and matched speed improvements remain unmeasured.


## Review the destination after a bounded navigation tail

A group of keyboard operations can finish while the application is still showing
a transitional frame. In public guarded mode, `status=completed` establishes the
program outcome and `feedback_status=captured` establishes a capture; neither
means the destination is ready. `wait_update` records a fixed delay, not an
application acknowledgement.

After navigating, inspect the returned destination before entering another form.
If the image is still transitional, request `interface_guarded_observe` for a new
read-only image. `interface_results` returns the retained old image and cannot
resolve whether navigation has since finished. Do not repeat uncertain navigation
just to recover feedback. Keep entered-value review separate from submission.

A [primary six-task trial](results/guarded-navigation-batch-primary-01/README.md)
combined URL entry and Enter, but needed four extra observations across five
navigations. It completed all six values exactly once using 28 calls, versus a
24-call plan. This candidate remains on hold as a default recipe; its nominal
call reduction does not establish a speedup or token savings. Different explicit
observation conditions can be evaluated in a fresh allocation without rewriting
this result.


## Exact placement through a visible numeric field

When an application exposes a position field, it can provide an explicit route
for a document-coordinate target. Review the selected object and field units,
select the whole value and confirm the selection, enter the requested value,
then inspect the resulting position and dimensions before saving. Use coordinates
from the current image; do not copy another session's toolbar coordinates.
This remains ordinary GUI input chosen by the primary model.

[Primary Inkscape use](results/inkscape-numeric-primary-01/README.md) saved one red
40x30 rectangle at X80/Y50 through the visible X field at 118% zoom. It took six
MCP calls including close, with no extra observations or input replay. This is
one functional example, not evidence of faster operation than dragging. A
[preceding drag](results/inkscape-current-primary-01/README.md) had different
success criteria and showed that pointer distance did not equal object distance.
Neither recipe implies automatic geometry verification or a universal motor gain.

## Keyboard layout changes in persistent X11 sessions

The X11 backend refreshes queued keyboard mapping changes before programs with
keyboard operations. Underscore follows the current supported keymap level;
held keys retain their original physical code for release. This does not cover
arbitrary layouts, IMEs or mapping changes during a program. Review the returned
text image and saved outcome when correctness matters.

[Primary same-session JP-to-US use](results/keymap-primary-use-01/README.md)
saved and visually reviewed two strings through the portable public MCP runtime,
then independently checked the final file after close. The record includes a
setup failure and measured preflight overhead; it does not claim faster model
interaction or general desktop reliability.

## Optional paced-dispatch summaries

For supported successful public paced-text dispatches, explicitly combine
`detail="brief"`, `compact=true` and `report_refs=true`. Images and outcome
fields remain present; duplicated programs, validated wait details and expansion
maps can be omitted from a marked partial receipt. Follow
`presentation.retrieve` for the full retained report without replaying input.
Full output remains the default, and failures or unsupported shapes stay full.

[Fresh primary use](results/public-paced-brief-01/README.md) exercised both brief
images and full retrieval. The primary detected an initial missing character in
the returned image and made an explicit repair. This option reduces serialized
text for eligible replies; it does not establish token savings, task success or
faster interaction, and the retrieval itself adds a call.

## Clicking a field before entering text

Treat field activation and text entry as separate decisions when the recipient is
uncertain. Click the field using current geometry, inspect useful feedback, then
enter and review the value before saving or submitting it. A screenshot without
visible recipient evidence does not establish that the field is ready. If the
application offers no useful readiness evidence, that uncertainty remains.

A single click/text batch can outrun the application's handling of the click.
`focus` verifies an X11 window ancestry, not the application-internal editor;
`wait_update` is an explicit fixed delay, not a ready acknowledgement. Existing
integration tests use a 50 ms post-click wait, but that is not a universal safe
threshold and the runtime does not insert it automatically. Paced text gaps are
between characters and do not settle the click before the first character.

[Retained click-recipe intake](results/click-readiness-intake-01/README.md)
verified that the earlier successful click study included cooperative app turns
between activation and text. Its results therefore do not validate removing those
boundaries. The [public primary trial](results/public-paced-brief-01/README.md)
retains a missing first character, visual detection and an explicit repair.
Do not replay an uncertain whole input program to recover a missing prefix.

For a known click-to-text timing problem, an explicit bounded pause can be placed
between mouse release and text, using the existing operations:

```json
{"op":"wait_update","timeout_ms":50}
```

This is a caller-selected mitigation, not a readiness condition. In a fresh
[public MCP integration comparison](results/click-text-comparison-01/README.md),
the known Tk fixture saved the exact text in 6/6 cases with this pause versus 2/6
without it; four missing-prefix outcomes are retained. The pause added about
54.4 ms to median local tool return. This does not establish a universal 50 ms
threshold or faster end-to-end use, and it does not replace value review.

[Primary two-editor use](results/click-primary-01/README.md) applied the explicit
pause through the portable public MCP runtime, reviewed each unsaved value, then
saved in a separate program. Both final files were exact with six calls, five
images and no repair. This is functional evidence for the explicit workflow;
reviewing before save adds a decision boundary and is not a speedup claim.

## Optional successful-dispatch summaries

`interface_dispatch` and retained `interface_results` accept `detail="summary"`
with `compact=true, report_refs=true`. This opt-in partial view supports known
successful public dispatch reports, including short nonpaced save programs.
Default `detail="full"` and the existing paced `detail="brief"` remain unchanged.

The receipt schema is `agent-interface/receipt-view-dispatch-summary-v1`.
Read `receipt.execution_summary` for execution times, emissions, all capture,
release and activation records, completed operation count and fixed-wait totals.
Images, outcome fields, target/session state and call identity remain unchanged.
A retained lookup without a live session snapshot keeps its historical session
at `receipt.reported_session`; it does not mint a current binding or authority.
Source programs, expansion mapping, per-wait timestamps, completed indices and
duplicate receipt/session metadata are omitted. The source digest identifies the
retained full report, not the summary. This does not assert task success.

Follow `presentation.retrieve` to obtain the same call with `detail="full"`
without replaying input or taking another capture. The lossless receipt decoder
deliberately rejects the partial summary schema. Failed, incomplete, unfamiliar
or inconsistent omitted records stay full, as do reports that would not shrink.
A fixed wait remains a delay, not an acknowledgement of an application update.

[Primary summary-mode use](results/public-summary-01/README.md) exercised paced
input, a short save, full retrieval and an unchanged full refusal. The two actual
successful replies used 45.3% fewer canonical JSON bytes than their full views
and 27.8% fewer than the previous brief option. This is not measured token/cost or
speed improvement; the full lookup itself adds a call. The record includes the
retained-session correction and its failed-before/passing-after checks.

## Primary use with summaries and returned host attempts

[Current-main primary examples](results/current-primary-summary-01/README.md)
combine public summary dispatches and `reply.attempt` presentation in a small
entry task and LibreOffice Calc, including explicit format-dialog selection.
Both saved effects were independently checked after control ended. In Calc,
a completed Return plus a 100ms wait still captured the dialog; a fresh read-only
inspection confirmed it had closed. Do not repeat uncertain input merely because
the result image has not yet changed. This is scoped usability evidence, not a
matched speed, token/cost or generic readiness result.

## Select feedback context explicitly

Use the existing capture region to keep the evidence needed for the next decision
readable. A small cell view may suffice to check entered numbers; a format dialog
needs its header and choice buttons; final save confirmation may need a wider
view. Preserve the returned frame, origin, dimensions and original image hash.
For `screen_physical_px`, translate local image coordinates by the returned origin.
`window_client` uses a different frame. A region view does not grant target or
input authority, and completion cues outside it remain unknown.

Persistent public MCP can request read-only post-release target inspection and
an explicit region in the same dispatch using
[`inspect_after` options](cli_v1/MCP.md#explicit-post-dispatch-target-context-and-capture-region).
The public Python API uses `MCPSessionOwner.inspect_after_dispatch` with
`screen_region` and an optional `wait_ms`, then `present_result` returns its
selected original ImageContent and reference. CLI text alone does not present
pixels: assistant hosts must forward the image block as an image and keep the
outcome metadata. Direct original forwarding is useful plumbing, but does not
by itself prove the primary saw every pixel.

[Current primary region admission](results/explicit-region-admission-01/README.md)
completed a fresh Calc save with seven commands, three input programs and one
extra full-frame observation. Initial cells and the format modal were readable;
a repeated modal image was used only after exact equality to the immediately
reviewed original from that same owner. Final100ms feedback still showed the
old dialog, so the primary withheld completion and observed separately.
[The prior direct-forwarding STOP](results/direct-selected-image-01/README.md)
remains retained. These are bounded integration results, not a general image
compression, token-cost, latency or human-speed claim. Region selection remains
explicit and defaults remain unchanged.


### Conditional Inkscape continuation on the public owner

The [finite primary comparison](results/inkscape-conditional-live-01/README.md)
connects the existing shared core graph to the same public input owner as a strong
ordinary callback. Both draw, verify a fresh post-release image, then conditionally
Save without a model resumption between the actions. Both stop before Save for an
unknown fixed layout cue. Independent saved SVG scoring accepts both positive
cases; the negative controls retain the original empty SVG. This is a scoped
application-authored public adapter, not qualification of the guarded X11 graph
adapter on Inkscape. Same inputs/captures/primary roundtrips and single-case timing
do not establish a graph advantage. Keep the ordinary route/default and existing
efficiency HOLD. Use explicit source/lease/deadline/release checks and independently
score persistence; neither the pixel cue nor graph task verdict certifies saving.


### Program emission accounting

For a dispatch review, `outcome_summary.program_emissions` now exposes the
explicit current-program count from `result.execution.program_emissions`, or the
existing top-level refusal count. Valid duplicate copies must agree; malformed
or conflicting copies return null. Missing counters remain absent. This field
is recorded evidence, not a claim of no input, verified release or task success.
On the X11 backend, `execution.emissions` is cumulative for the backend connection
while `execution.program_emissions` is the current execute-call delta, including
cleanup emissions during that call. Sum program deltas, not cumulative totals.
Counts outside a program, such as a later owner close, require their own receipt.
The retained Inkscape sequence reports cumulative10→14 but program10+4=14, not24.
Raw reports and their hashes remain unchanged; lookup/review does not execute input.

[Program-emission regression evidence](results/program-emission-review-01/README.md)
includes the original-counter recheck, portable archive, and native test logs.


### Bounded selection, movement and conditional saving

A guarded compiled method can include selection as its first action when a
fresh application-specific selection cue is available. Match the reference's
returned offset to the action using that reference: a rectangle reference and
keyboard context can have different region sizes and offsets. Keep texture,
source, scope, admission, deadline and release checks; a fixed post-click wait
is not a selection acknowledgement. Stop on an unknown or failed effect before
moving or saving. Independently score the persisted document after control ends.

The [first full-method comparison](results/inkscape-single-method-01/README.md)
retains a compiled selection failure: normal tasks succeeded1/2, although both
undertravel controls withheld Save. A separate, frozen
[interior-point successor](results/inkscape-interior-point-01/README.md) used a
visibly interior click point with a textured32x32reference, rather than a
boundary point with16x16context. Both normal routes saved the correct rectangle,
and both controls stopped before Save. The point and reference context changed
together; the prior failure's actual input recipient/readiness/cause is unknown.
These results do not establish generic selection detection or spatial robustness.

The successor compared the full three-action graph against a strong ordinary
conditional callback. Both normal routes used3input programs,37program emissions,
13captures,5callercommands and2primaryimages. Local method time was704ms ordinary
and845ms compiled in one case each: no graph efficiency advantage or human-tempo
claim follows. Actual primary usage is reconstructed for each explicit joint
window, including construction and verification; nested method windows exclude
other task decisions and overlap those totals. Evolving context/cache prevents
a causal token-saving comparison. Keep current defaults and the efficiency HOLD.
The [selection-cue development preflight](results/inkscape-selection-gate-preflight-01/README.md)
uses historical labeled frames; it is not held-out visual qualification.


### Compose batch registration with the owned capture directory

The public Python `GuardedSessionOwner.invoke_guarded('guarded_mint_many', ...)`
can register multiple explicitly grounded references from one inspected source.
Use each returned offset and inspect complete registration before input. Partial
registration is not atomic: retain the registered prefix and stop uncertain input.

This public owner configures capture artifacts under the supplied call directory.
A custom continuation using its bridge must keep the next capture directory and
the directory passed to `present_result` aligned. Do not relax image confinement
or treat an internal successful method receipt as delivered visual feedback.
The [first composition](results/inkscape-public-batch-mint-01/README.md) saved the
correct file but failed final presentation because the adapter used the previous
bridge directory. Its allocated failure and three unallocated cases are retained.

A [separately frozen successor](results/inkscape-public-batch-mint-02/README.md)
explicitly used a method-call capture/presentation directory. Both ordinary and
guarded graph routes saved the correct normal task, and both undertravel controls
withheld Save; the primary reviewed all eight original images. Each case used
four caller commands instead of the historical five with separate registrations.
The method, inputs, effect gates and confinement rules stayed unchanged. This is
a public Python owner composition, not a compiled MCP tool or MCP transport test.
Actual primary usage includes construction, failure and repair; the historical
comparison and evolving context/cache do not prove token or speed gains. Keep
production defaults and the efficiency HOLD.


### Candidate: bounded graph through the public Python owner (live HOLD)

This draft candidate has no successful normal live qualification yet. Both
allocated cases stopped at unresolved selection, before movement or Save.
See the [retained failure and accounting report](results/public-owner-compiled-primary-01/PUBLICATION.md).

After explicitly opening `GuardedSessionOwner` and grounding its references,
call `owner.run_compiled(interface, bindings, call_root=fresh_directory,
perceive=read_only_callback, verify_effect=read_only_callback)`. An optional
`cancelled` callback uses the existing graph cancellation contract. Calls are
serialized by the caller; this synchronous API does not add a scheduler or MCP
tool. The owner must be open, reviewed and recovered. The call directory must
be new; existing directories refuse before graph execution.

The existing graph performs its scope, dependency, admission, deadline and
release checks. Raw captures and graph evidence remain in the owner's bridge
directory; image artifacts use this call's images directory. The result returns
`method_receipt`, `feedback`, `session`, `task_success=null` and
`replay_allowed=false`. Feedback presents the last capture actually used by
this graph, without an additional observation. A graph with no observations
returns feedback=null rather than presenting a previous image.

Read method and feedback outcomes separately. If presentation is unavailable,
the completed prefix remains in method_receipt and the owner requires review.
An exception also requires review and retains cleanup duty on the same owner;
close attempts release even when input may have happened before the exception.
No automatic retry, re-grounding, restart or recovery reset follows. Callbacks
are trusted caller code, not generic perception or independent task scoring.
Independently verify saved effects, and retain the returned wrapper evidence.
No hard real-time bound, matched latency or token advantage is established by
this API addition. Existing input/MCP schemas and defaults are unchanged.
