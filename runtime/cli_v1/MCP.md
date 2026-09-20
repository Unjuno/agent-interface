# Public one-shot MCP transport

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
commands do not import MCP. Missing MCP dependencies affect only `mcp` mode.

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

- `interface_observe(target, frame, region, compact=false)` takes one explicit
  read-only capture. Region is `[x,y,width,height]` in the selected frame.
- `interface_dispatch(program, current_observation_seq,
  current_binding_revision, compact=false)` performs one public dispatch. Include
  an `observe` operation if its result should contain an image. Explicit bounded
  key repetitions use the same public compiler and failure-source mapping.

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

`interface_results()` lists the newest 20 calls issued by this running server,
most recent first, with call IDs, operation names and worker states. Use
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
