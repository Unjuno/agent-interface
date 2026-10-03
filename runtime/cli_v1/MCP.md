# Public MCP transport

This optional adapter exposes the existing public `observe` and `dispatch` APIs
to an MCP host. It returns metadata as text and the selected PNG as a separate
image block, so the host need not parse base64 out of CLI text. It launches no
model, application, display or research allocation.

Use a Python environment with `mcp==1.30.0`, plus the backend dependencies listed
in the CLI guide. Launch from a repository checkout or use the portable zipapp's
explicit `mcp` mode. For Linux/X11, run in WSL or Linux with python-xlib
and Pillow installed in that same environment and an existing display.

Before host setup, run `python -m runtime.cli_v1 doctor --check-dependencies`
or `python agent-interface-runtime.pyz doctor --check-dependencies` with the
same interpreter the host will launch. Module discovery is not a live connection
check; separately verify the target/display and any application dependencies.

Configure the MCP host to launch the equivalent of:

```sh
python -m runtime.cli_v1.mcp_server \
  --targets /absolute/targets.json \
  --output-directory /absolute/session-receipts \
  --display :99
```

The equivalent portable command works outside a checkout:

```sh
python /absolute/agent-interface-runtime.pyz mcp \
  --targets /absolute/targets.json \
  --output-directory /absolute/session-receipts \
  --display :99
```

The archive includes the adapter, not its third-party dependencies. Ordinary CLI
commands do not import MCP. Missing MCP dependencies affect only `mcp` and `relay` modes.

Requests and reports use the CLI's temporary-file, flush/fsync, then replace
writer. The final report name is published only after the write completes.
A failed request write returns `REQUEST_PERSISTENCE_FAILED` with
`operation_invoked=false` and sends no input. A failed report write preserves
the action outcome in the immediate response, adds `persistence_error` and
`replay_allowed=false`, and sets the MCP error flag. Inspect the outcome even
when that flag is set: the action may have completed. The call registry still
reports the worker as finished, but a missing final report yields
`receipt_unavailable`; result lookup does not promote a temporary file or repeat
input. Temporary files remain for inspection. This shares the CLI's persistence
mechanism, not a guarantee of directory durability after a machine crash or
server-restart recovery. Storage flush cost has not been measured as a model
latency benefit.

For module launch, set the host's working directory to the repository root.
For portable launch, use the absolute archive path. `targets.json` is a
nonempty mapping such as `{"editor":12345}`, with the actual native window ID
selected by the caller. IDs are loaded once at startup, not discovered or
refreshed automatically. Do not reuse an ID after its target lifecycle changes.
The host must actually start this server and expose its tools; writing this
configuration alone does not establish availability in an existing conversation.

On Linux, an explicit `--display` is used both for backend selection and for
opening the X11 connection, even when the MCP host does not forward `DISPLAY`.
It takes precedence over an inherited display without changing the process-wide
environment. With no explicit display, normal environment selection applies.

- `interface_observe(target, frame, region, compact=false, report_refs=false)` takes one explicit
  read-only capture. Region is `[x,y,width,height]` in the selected frame.
- `interface_dispatch(program, current_observation_seq,
  current_binding_revision, compact=false, report_refs=false)` performs one public dispatch. Include
  an `observe` operation if its result should contain an image. Explicit bounded
  key repetitions use the same public compiler and failure-source mapping.

- `interface_results(call_id=null, before_call_id=null, compact=false,
  include_image=true, report_refs=false)` lists calls or reads a retained result without input or
  capture. See the result-retrieval section below.

These three tools keep v1/v2 receipt selection with `compact=true` alone.
A consumer with the v3 decoder can explicitly set both `compact=true` and
`report_refs=true` to allow a duplicate report to reference `source.raw_report`
in the same response. `report_refs=true` without compact mode is rejected before
operation scheduling. Images and outcomes are unchanged. A retained-result read
can change the receipt format without capturing or replaying the operation.

To read a v3 response directly, check `receipt.schema` is
`agent-interface/receipt-view-v3-report-ref`: its `receipt.report` is a marker,
and the complete report is `receipt.source.raw_report` in the same response.
`/source/raw_report` is relative to the receipt, not a filesystem path or a
request to another tool. Inspect `outcome_summary` for execution/release/cleanup
and the returned image for visible application state; the reference itself is
not evidence of task completion or freshness. Interpret only the declared v3
reference; similarly shaped objects elsewhere remain ordinary data. A caller
that does not understand this format should leave `report_refs=false`.

[Primary v3 use](../results/mcp-report-refs-use-01/README.md) records one
SDK-mediated input/save and read-only result comparison, including identical
images and exact reconstruction. It does not establish token or speed savings.

[Two-application compact use](../results/compact-mixed-app-01/README.md) retains
a Calc/Inkscape trial with 11 v3 receipts, verified close and independent saved
file checks, including one text-entry correction. To opt in, pass both flags on
each supported call, for example:

```json
{"target":"calc","frame":"screen_physical_px","region":[0,0,1280,800],"compact":true,"report_refs":true}
```

Use this argument object with `interface_observe`; `interface_dispatch` accepts
the same two presentation flags alongside its program and source assertions.
Inspect the image and outcome separately. In v3, activation details remain at
`receipt.source.raw_report.result.execution.activations`; do not interpret the
reference marker as missing execution evidence or repeat an operation to read it.
Management calls retain their own format. One offline replay reduced serialized
text for 10 observe/dispatch reports by 30.09%, excluding image blocks and five
management calls. Actual model tokens, cost and latency were not measured.

`interface_validate(program)` optionally checks a draft using the same static
inspector as CLI `validate`, without opening a backend or issuing input. It
returns static validity, required capabilities or bounded diagnostics with
operation positions where available. Invalid drafts set `isError=true` and
`static_valid=false`. Even an expired lease may be statically valid: this is not
a runtime admission. A nesting-limit failure returns `status=input_error`,
`error=INPUT_NESTING_LIMIT`, `static_valid=null` and `isError=true`, matching the
file inspector's unassessed-input distinction. Validation does not constitute
a capability, freshness, authority or task-success check. Dispatch still performs
its existing checks; calling validation first is optional. It creates no action
call ID, image, persisted request or `interface_results` entry. The usual fixed
server startup configuration is still required.
See [receipt formats](README.md#compact-received-report-references).

The dispatch tool advertises the program envelope, bounded operation examples and
lease clock requirement in its `program` description. This is discovery metadata,
not a new parser: dictionaries, extension fields and malformed-program receipts
still pass through the existing public compiler and admission path. No lease or
operation defaults are inserted. Schema size and model usability have not been
benchmarked; this does not claim a token reduction.

### Choosing the observation frame on X11

`window_client` reads the target's client drawable. Its region starts at that
client's origin, excluding window decorations. An overlapping dialog belongs to
another window and may appear as a black or missing area in this capture.
Repeating the same window-client capture does not necessarily reveal the dialog.

`screen_physical_px` reads the display at the explicitly supplied display
coordinates. It includes the visible windows within that region, so it can show
an overlapping dialog together with the application. Select the intended display
region; the tool does not automatically widen the capture or discover its bounds.
Do not reuse client-relative coordinates as display coordinates without conversion.
These frame meanings also apply to `observe` operations inside a dispatch program.

In [primary Calc use (#3667)](https://github.com/Unjuno/agent-interface/pull/3667),
two window-client observations showed a black central area. A subsequent explicit
screen observation revealed the Tip of the Day dialog and its OK button. This
motivates the tool guidance; it is not automatic occlusion detection or a measured
latency improvement. In either frame, an image may still precede the application's
redraw, and reading a retained result does not capture a newer image.

Programs, leases and current observation/binding values retain the public API's
caller-supplied meaning. This adapter issues no source authority and is not a
persistent desktop session manager. Each API call opens and closes its own
backend session. It does not solve recovery across reconstructed sessions.

Only one call runs at a time. An overlapping call returns `busy` with
`operation_invoked=false`; it is not queued or replayed. A transport timeout or
cancellation does not prove that a dispatched action stopped. The worker can
finish and retain its receipt after the caller disconnects; inspect the retained
result and actual application state before making another decision. Do not
automatically restart the server or replay an uncertain action.

Each admitted transport call creates a unique directory containing request.json,
report.json and any captures. The exact raw result is also retained in the review
envelope. A request persistence error prevents the API call. A report persistence
error after execution is reported alongside the action result; it never causes a
retry. A review failure preserves the raw report. Requests/results may contain
typed text and screenshots; choose an output directory suitable for that data.

CLI and MCP share `review.present_result` for result presentation. If review
itself raises, both return `schema=agent-interface/review-v1`,
`image_status=needs_review`, `image_error`, `raw_result`, and `outcome_summary`.
MCP adds its `call_directory` and any persistence error outside this common
envelope. Direct API users may call the same helper. This replaces the initial
MCP-only `status/review_error/raw_report` fallback, keeping the CLI fallback keys.

Inspect action status, partial-effect uncertainty, cleanup and image status
separately. A returned image is not a redraw or task-completion acknowledgement.
Compact mode selects reversible event references only when their JSON is smaller;
it does not establish a token, cost or latency reduction.

The shared integration runner includes API forwarding, strict argument checks,
duplicate-call exclusion, persistence/review failures, and real stdio discovery
with a rejected no-GUI request. These are transport/contract checks, not a primary
model live-use result or a performance comparison.

## Recover a retained result without resending input

For an outcome-only check, use
`interface_results(call_id="...", include_image=false)`. The default is `true`.
When a retained image is available, the opt-out omits its native image block and
adds `image_delivery="omitted_by_request"`; the image reference, outcome and raw
receipt remain available. `image_status` still describes the retained image, not
whether a block was sent. A later default lookup can return the same image.
This option does not skip image validation, hide missing-image errors, refresh
the screen or replay input. It controls delivery only; no model-token, cost or
latency reduction has been measured. Call listings contain no images either way.

Observe and dispatch result envelopes include `call_id`. Pass it directly to
`interface_results(call_id=...)`; parsing `call_directory` or listing calls first
is unnecessary when the original response is available. A retained result returns
the same ID. This identifies a server call, not a fresh image or successful task.

`interface_results()` lists the newest 20 calls issued by this running server,
most recent first, with call IDs, operation names and worker states. If
`next_before_call_id` is non-null, pass it as `before_call_id` to read the next
older page. Pages continue strictly before that ID even if newer calls arrive;
new calls appear when listing from the beginning again. An unknown cursor is an
error, not an empty history. Do not combine `call_id` and `before_call_id`. Use
`interface_results(call_id="...")` to inspect a specific call and its original
arguments. Running calls return `pending`; finished calls reread the saved report
and return the common review envelope and any native image block. `compact=true`
uses the existing reversible review projection. Neither form invokes a backend.

After a lost response, match the retained arguments to the intended request before
interpreting the result. The call ID is a lookup reference, not an idempotency key
or permission to resubmit. A finished worker does not establish task success.
Missing or unreadable reports return `receipt_unavailable`; unknown IDs return
`unknown_call`. No action is replayed to fill a gap. Missing images retain the
normal review failure and original action outcome.

Only IDs created in this server process can be read; arbitrary filesystem paths
and prior-server calls are not accepted. A server restart loses this in-memory
index, while on-disk receipts remain for explicit file review. Calls do not expire
from the index during the process lifetime; deployments should account for its
memory use. This is result retrieval, not automatic restart recovery or polling
of application state. Current `operation_invoked=false` describes the retrieval
call, not whether the retained original call emitted input.

By-ID results also retain the original call's `backend_attempted` and
`persistence_failure` (`null`, `request`, or `report`) in `call` for pending or
unavailable results, or `retained_call` for a readable report. These are in-memory
process facts. `backend_attempted=true` marks entry to the backend attempt, not
input emission, execution success or task effect. A finished call with
`backend_attempted=false` and `persistence_failure=request` stopped before that
attempt; a report-save failure may follow input. A running call with false can
still proceed later. An unavailable receipt explicitly has `replay_allowed=false`.
These fields do not grant replay permission or survive a server restart.


## Opt-in scoped X11 mode

Use `--session-mode guarded-x11` for one explicitly configured X11 target and
image-grounded aliases on one retained connection. It reuses the shared
`runtime.guarded_x11_v1` implementation and the public request journal, busy
rejection, result retrieval and close lifecycle. It selects no actions and
requires no helper model. The default remains one-shot.

```sh
python /absolute/agent-interface-runtime.pyz mcp \
  --targets /absolute/one-target.json \
  --output-directory /absolute/fresh-receipts \
  --display :99 --session-mode guarded-x11
```

Install MCP, Pillow and python-xlib in the launching interpreter. The target
file must contain exactly one explicit positive window ID, for example
`{"browser":6291459}` with the caller's actual ID. The server does not launch
an application/display or discover a target.

1. Call `interface_guarded_observe()` and view its image.
2. Call `interface_guarded_mint(alias, source_sequence, point, region_size)`
   using that returned `source.sequence` and an image-grounded screen point.
   `region_size` is a two-integer pixel size, each 4..96. Flat regions refuse.
3. Call `interface_guarded_input(alias, offset, tail, interaction="click",
   observe_after=true)` with the returned alias/offset. `keyboard` guards the
   same context without clicking. Tail operations follow the bridge's bounded
   text/key/wait/observe contract. A successful input response normally contains
   its result and a fresh image; inspect both before deciding the next action.
4. Re-ground explicitly after a stale-reference refusal. An uncertain input or
   failed post-input capture is not permission to repeat the input.
5. Use `interface_results` to read history without input or capture, then
   `interface_close` to release held input and close. History remains readable
   after close; its session snapshot is historical, not the live session state.

Ordinary `interface_dispatch`/`interface_observe` and transient-family tools are
not registered in this mode. `interface_validate` remains available for static
program inspection, not alias admission. Guarded results use full reports even
with compact retrieval flags; `report_refs` still requires `compact=true`.

`interface_guarded_review_window(window_id)` explicitly reviews the focused
window and revokes all prior aliases, even on a failed review. A successful
review returns an image/source for new aliases. This is the bridge's focused
window contract, not authenticated application identity or transient-family
review. Aliases expire under the bridge's existing bounded lifetime and remain
session-local. Closing or restarting does not revive them.

The immediate capture does not wait for redraw or establish semantic completion.
`wait_update` is a bounded delay. CTRL+A emission does not prove selection, and
address-field focus does not prove the application is ready for text. Review
entered values before consequential submission. No global pacing default changes.

[Primary use and retained evidence](../results/guarded-mcp-primary-02/README.md)
records six exact saves, a stale-alias refusal before input, explicit recovery,
source-bound review receipts and result retrieval after close. The earlier
interrupted trial is retained separately. This establishes scoped integration
and usability, not matched performance, token savings or human-like tempo.

## Brief guarded-input details

`interface_guarded_input(..., detail="brief")` optionally summarizes repeated
normal exact-match guard records. The default is `detail="full"`. This adapts the
positive-only native brief-review approach to public guarded reports; it is not
a lossless codec. `result.guard_summary` replaces `result.guard_checks` only for
known completed results with an image, no recovery, verified empty releases,
completed waits and unmoved exact-region guards. Other result fields, observation
identity and image stay unchanged. Failures, persistence errors, translations,
unknown guard/result extensions and unsupported shapes retain full detail.

The `presentation.retrieve` object gives an exact `interface_results` call with
`detail="full"` and `include_image=false`. It reads the original retained report
without input or observation. Result retrieval also accepts `detail="brief"`;
this applies only to guarded reports and leaves other modes unchanged. Raw
`report.json` is never replaced by the summary. A caller must inspect release,
feedback and task state separately; a brief normal receipt is not semantic success.

The option can reduce serialized metadata for repeated normal guards, but this
is not evidence of fewer actual model tokens, lower cost or faster decisions.

### Unknown top-level arguments

Public MCP tools reject unknown top-level argument names before invoking the operation or opening the backend. Discovery advertises `additionalProperties: false`. For keyboard-only guarded input, use `interaction: "keyboard"`; `pointer: false` is not an argument. Do not infer accepted semantics from an unrecognized flag. This check does not alter nested program or tail validation. Validation errors may be plain text from the SDK; host renderers must not assume every text block is JSON.


### Register multiple references from one image

In guarded-x11 mode, interface_guarded_mint_many accepts one source_sequence and 1..8 references, each containing alias, point=[screen_x,screen_y], and region_size=[width,height]. Use the exact delivered source you inspected. Each alias must match [a-z][a-z0-9_]{0,31}; points are integer pairs and region dimensions are 4..96 pixels. Unknown nested fields and duplicate aliases refuse before any registration. This reuses the existing bridge mint operation; it does not capture, click, infer targets, acknowledge UI state, or weaken later input guards.

Successful single mint replies and each successful `minted` entry include
`lifetime`: `clock="time.monotonic_ns"`, `minted_ns`, `expires_ns`,
`capture_freshness_ms` and `authority_granted=false`. Compare the deadline only
with `interface_clock` from the same running execution host. References expire
300 seconds after minting; each input still independently checks fresh captures,
focus, exact pixels and the point immediately before pressing. A deadline in the
future is not evidence of pixel validity or input authority. Retained results
return the original lifetime and never renew it. After a pause, explicitly
observe and review the screen, then mint a new unique alias if needed; there is
no automatic renewal, input retry or extension of the original reference.

Successful entries return alias/offset pairs under minted. Registration is sequential and not atomic. If minting raises, the reply retains earlier successes, identifies failed_index and failed_alias with failed_alias_state="unknown", and lists unattempted_aliases. Registration may have occurred before a persistence failure, so do not replay the batch or reuse the failed alias. Inspect the outcome and explicitly choose fresh references if needed. Full retained results remain available without reminting.

This transport option reduces the number of registration requests for a supplied group by construction. It does not establish lower model latency, token cost, or generic task completion; primary GUI validation and matched measurement are separate requirements.

### Optional local observation references

Guarded observe/input and interface_results accept observation_refs=true (default
false). Exact duplicate observation_report.observation metadata may become
`{"observation_ref":"/source/native"}`. The complete source.native remains in the
same response; only the path explicitly listed in observation_references is a
reference. Other reference-shaped values are literal. Images and raw reports are
unchanged, and the option never captures or sends input itself.

Use runtime.cli_v1.receipt_references.expand_guarded_observation to reconstruct
the view, or request the retained call with observation_refs=false. To retrieve
all guard detail too, use detail="full". Combining this lossless reference layer
with detail="brief" does not make brief guard summaries lossless. Refused and
persistence-failed replies remain literal; small/nonduplicate reports do too.

## Opt-in paced-dispatch brief view

For public dispatch, add `detail="brief"` together with `compact=true` and
`report_refs=true`. Full is the default. Supported successful paced-text
dispatches can omit duplicated source programs, per-wait records and expansion
mappings while retaining outcomes, release evidence, images and session state.
The wait summary describes fixed delays, not detected application updates.

A brief receipt uses `agent-interface/receipt-view-paced-brief-v1`.
Its partial report is at `receipt.source.report_projection`; it is not a
lossless v3 receipt and must not be passed to the v3 expansion decoder.
Follow `presentation.retrieve` to call `interface_results` for that exact
call with `detail="full"`. Retrieval never executes input again.
The original report and images remain retained in the current server process.
Failures, missing evidence, unsupported shapes and non-smaller projections stay
full. This is an explicit presentation option, not proof of task success or
measured token/cost savings.

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

## Optional target inspection after public dispatch

In `persistent-x11` mode, `interface_dispatch(..., inspect_after="app")` can
request the existing focused-target inspection after that one dispatch. The name
must be a configured target; unsupported modes and unknown names reject before
input. Omission preserves the existing behavior.

`post_dispatch_inspection` is separate from the execution outcome. Inspection
runs only after completed dispatch with verified released keys/buttons and no
input recovery requirement; otherwise its status is `skipped`. Inspection errors
preserve the original input result. Never replay input to recover this metadata.

The context contains a candidate `review_request` when available. The primary
must review the evidence and explicitly call `interface_review_target`, which
rechecks identity, expiry and binding revision. Inspection does not focus,
select a target, advance the binding revision or capture another image. Its
metadata is sampled after dispatch and is not atomically bound to the returned
image. Request a new image when the visual state is uncertain.

The full report persists this context. `interface_results` returns the same
historical data and does not inspect again or renew the one-use review ID.
Successful inspection metadata is preserved in full by `detail=summary`,
including expiry and any extension fields. Inspection errors, skipped inspection
and mismatched duplicated context retain the full response. `detail=brief`
also retains the full response for enriched reports. This opt-in trades
additional metadata and inspection time against a possible separate tool call;
no latency or token benefit is established yet.

Target inspection resolves a configured X11 child/widget ID to its first managed ancestor using at most 64 window IDs. For such targets, evidence includes `configured_target_path` and `managed_family_root`, while `family_root` retains the configured ID. The focused window must still belong to that managed transient family. Missing, destroyed, cyclic or excessive ancestry refuses inspection. The path is rechecked with the rest of the evidence during explicit target review; changed ancestry invalidates that review. This metadata lookup does not change the input binding or grant authority. See [earlier primary evidence](../results/post-dispatch-inspection-01/README.md) for the child-ID failure that motivated this support; those historical results remain unchanged.

### X11 key spelling

Use `{"op":"key_chord","keys":["Home"]}` for a Home tap and `{"op":"key_chord","keys":["CTRL","s"]}` for a chord. Held input uses `key_state` with `key` and `down`; `key` is not an operation name. X11 keysym names are case-sensitive: `Home`, `End`, `Left`, `Right`, `Up`, `Down`, `BackSpace`, `Delete`, `Insert`. The existing aliases `CTRL`, `SHIFT`, `ALT`, `ENTER`, `TAB`, `ESC`, `SPACE` are also accepted. The actual layout must still map the named key; static validation alone does not establish that.

For common uppercase misspellings, an unmapped-key refusal gives a spelling hint. It does not dispatch the suggested key, retry input, or change held-key identity. Read the execution outcome before deciding a corrected action. This guidance follows the retained `HOME` refusal and explicit `Home` correction in [primary child-target use](../results/managed-target-ancestry-01/README.md).

## Portable JSON-lines relay

For hosts that consume explicit JSON-lines requests rather than acting as an MCP client, the same archive provides a sequential adapter:

```bash
python3 runtime.pyz relay -- --targets /absolute/targets.json --output-directory /absolute/new-calls --session-mode persistent-x11 --display :99
```

Pipe stdin/stdout; terminal stdout is refused to preserve exact image JSON bytes. Install the same optional `mcp==1.30.0` dependency used by MCP mode. The relay launches `mcp` from that exact archive using the same Python executable; no research checkout, research allocation or native_start tool is involved. Source development also supports `python3 -m runtime.cli_v1.mcp_relay -- ...` from a checkout.

Send UTF-8 JSON lines without a byte order mark. The relay reads an OS pipe's
binary stream and decodes each line strictly as UTF-8 before JSON admission,
independently of the standard stream's locale encoding. Invalid UTF-8 and
UTF-16/32 byte inputs are refused without consuming an ID or entering the SDK.
Valid Unicode keys and values retain their decoded meaning, including equality
between a literal character and its JSON escape. Already decoded text inputs
used by source callers retain their existing text contract. An error after SDK
entry still consumes the accepted ID and requires reconciliation without replay.

Each line is exactly `{"id":1,"tool":"list_tools","arguments":{}}`, followed by IDs 2, 3, and so on for accepted calls. Public `interface_*` tools are forwarded unchanged, including image blocks and full/summary options. Inspect discovery to choose a tool. A refused envelope consumes no ID and reports `dispatched:false`; an accepted request consumes its ID before the SDK call, even if the outcome becomes unknown. Never resend an accepted ID or replay uncertain input. `sdk_entry_ns` and `sdk_return_ns` are execution-host monotonic boundaries, not model latency.

Every JSON object must have unique decoded keys, including nested program and
argument objects. Duplicate keys are refused before dispatch or ID consumption,
even if their values agree or one key uses a Unicode escape. Repeated keys in
separate objects and distinct case-sensitive keys remain valid. Numeric values
must decode to finite numbers; an exponent that overflows the float decoder is
also refused before dispatch. Numeric-looking strings remain strings.
If JSON decoding exceeds the interpreter's recursion limit, the line is refused
without consuming an ID; the relay remains available for the next request.
This does not promise support for arbitrarily deep JSON.

Call `interface_close` explicitly and inspect release/cleanup results before closing the pipe. EOF is a disconnect, not a task completion or application-cleanup guarantee. Keep stderr separate from the JSON-lines stream. This adapter does not add a model, queue, automatic retry, task policy or performance claim. The older research relay remains unchanged for frozen research callers.

### Program-local X11 target selection

Every X11 dispatch containing `pointer_move` or `observe` must include `focus`
or `activate` before those operations in that same program. The operating
system may retain widget focus across calls, but the dispatch program's target
selection starts empty. A previous dispatch or `interface_observe(target=...)`
does not populate it. Preflight rejects a missing selection before executing
any program input; read the reported outcome and release result before deciding
on a corrected program.

For a split focus/input/save interaction, each program that ends with an
observation therefore needs its own explicit selection. `focus` preserves an
already focused descendant; it does not establish that a clicked widget has
processed the click or that text has arrived. Review the returned image/value
before committing. The refusal and separate corrected allocation are retained
in [portable relay self-use](../results/portable-public-relay-01/README.md).

A Node host can use the [sequential host API](../host_v1/README.md) to retain requests/replies and deliver exact text/image blocks without importing the research tree. Its two `.mjs` files are separate from the Python archive.


For retained public observe/dispatch results, `include_image=false` still checks
the image path, recorded digest and PNG signature, but skips Base64 encoding of
the validated PNG. Metadata and `image_delivery=omitted_by_request` remain the
same as an ordinary image-omitted lookup. Missing or altered images still produce
`needs_review`; the option does not bypass validation or capture a new frame.
Management/guarded result presentation retains its existing path. No measured
model-token, cost or useful-feedback latency benefit is implied.


### Metadata-only retained image review

`interface_results(call_id=..., include_image=false)` validates the retained PNG
without Base64-encoding an image block that would be discarded. This applies to
both normal and guarded/management result presentation. The response retains the
same recorded source and image status, with `image_delivery=omitted_by_request`
when a valid image is available; a changed/missing/invalid PNG still reports its
review error. No fresh capture, redraw acknowledgement or input replay occurs.
The default `include_image=true` continues to return the retained image.

[Guarded public-path regression and primary use](../results/guarded-metadata-no-encode-01/README.md)
records the forwarding repair and scoped checks. Avoiding this conversion does
not by itself establish lower model tokens/cost or measured response latency.

### Worker submission failures

A synchronous worker submission rejection returns `status=worker_submission_failed`,
`failure_phase=worker_submission` and `replay_allowed=false`. If the callable has
not entered, its admission is revoked: `operation_invoked=false`,
`input_dispatched=false`, `effect_status=none`. It creates no operation call ID,
backend session or retained operation artifact. Capacity becomes available for a
new explicit call once the host's executor is usable; the server does not replace
the executor or retry the rejected request.

If callable entry raced with a submission error, the response instead preserves
`operation_invoked=true`, `input_dispatched=null`, `effect_status=unknown`. The
running worker keeps the admission slot until its existing finalization; inspect
retained calls before deciding how to continue. This does not authorize replay.
A terminal accepted future without callable entry also revokes only pending work;
SDK-level errors may still be returned. Cancelled transports continue to shield
accepted work, and overlapping calls remain busy rather than queued input.
## Execution clock without a new WSL process

`interface_clock {}` samples `time.monotonic_ns()` in the same execution host
as this live MCP server. Use that sample when authoring an already authorized
absolute `expires_at_ns` for a new program. The response contains a stable
`server_instance_id` for this server's lifetime; a replacement server has a new
ID. Compare and keep that identity in your caller. Do not translate Windows
wall/monotonic time into the sample or reuse it across execution hosts.

For example, an explicitly authorized five-second validity window can be authored
as `expires_at_ns = sample.monotonic_ns + 5_000_000_000`. Receipt/presentation and
model waiting consume that window. An old sample is not renewed by reading
retained results, and a refused expiry does not authorize replay. Request a new
sample only when authoring a separately authorized new program after reviewing
current state. Keep the existing source/binding assertions and admission checks.

The clock call opens no backend and issues no lease, source sequence or input.
It has no arguments and creates no action call ID for `interface_results`.
The relay host can retain its exact request/reply. It does not prove freshness,
application readiness, task success, suspend continuity or hard-real-time timing.
A clock reply remains metadata even after an input session has closed; it cannot
reopen that session or clear a recovery block.

## Explicit post-dispatch target context and capture region

In `persistent-x11` mode, `interface_dispatch` accepts the existing optional
`inspect_after`, `inspect_after_region` and `inspect_after_wait_ms` arguments.
`inspect_after` names an actual configured target. Without a region, the
inspection returns target-review metadata only. With a region, it captures once
in `screen_physical_px` after completed input and verified neutral releases,
then rechecks the target evidence. The original input outcome is retained even
if this later inspection fails; do not replay the input to recover an image.
Unsupported modes/targets and malformed options are rejected before dispatch.

These are an option fragment to add to a complete authored dispatch request,
not a standalone input program or portable coordinates:

```json
{"inspect_after":"configured-name","inspect_after_region":[0,165,290,116],"inspect_after_wait_ms":100}
```

Choose bounds from the actual layout and the cues needed for the next decision.
The wait is an optional integer0..1000ms, defaults to no added wait, and occurs
only after verified release. It does not extend the input lease or acknowledge
redraw. `capture_wait.update_observed` remains unknown. Metadata sampled after
input and captured pixels are not an atomic application-state guarantee.

For a successful selected later capture, `image_reference` identifies
`post_dispatch_observation_id`, the region and `capture_phase=after_dispatch_release`.
Forward the selected original image block with its outcome/reference metadata.
A screen ROI local point[u,v] maps to screen[region.x+u,region.y+v] at original
pixel dimensions. Cropping does not rebind the target or issue action authority.
Use the explicit one-use `interface_review_target` request only after reviewing
its evidence; expiry/identity/revision are checked again. Retained lookup does
not renew it. If needed cues are outside a crop, explicitly request a wider
read-only observation; do not infer task completion from the cropped cells.

[Fresh primary region use](../results/explicit-region-admission-01/README.md)
used the public Python counterparts with small cell feedback, a larger format
modal view and full-frame final feedback. It saved149/857 correctly but still
needed one explicit final observation because the first final frame was stale.
[Direct-block failure](../results/direct-selected-image-01/README.md) preserves a
separate initial partial-presentation STOP. These cases do not qualify generic
render reliability, wait defaults, speed or token savings, and do not certify
provider MCP conversion of the Python route.
