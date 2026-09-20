# Native research session over MCP stdio

Optional thin adapter for a private native harness. Attach mode exposes
three named tools and returns complete compact receipt text plus the exact PNG
as a separate MCP image block. The model does not need to generate shell commands
or manually convert WSL image paths on an MCP host that supports image results.

Install into a dedicated environment:

```sh
python3 -m venv /tmp/agent-interface-mcp-venv
/tmp/agent-interface-mcp-venv/bin/pip install -r research/live_control/requirements-native-mcp.txt
PYTHONPATH=.:research/live_control /tmp/agent-interface-mcp-venv/bin/python research/live_control/native_mcp_v1.py --run-directory /absolute/path/to/existing/run
```

Use that command as a stdio server command in an MCP-compatible host. On Windows,
launch through `wsl.exe -d Ubuntu --cd /absolute/linux/repository --exec env
PYTHONPATH=.:research/live_control /tmp/agent-interface-mcp-venv/bin/python ...`.
Do not start a second harness or guess the newest run to attach. The host must
forward image content blocks. This repository does not auto-edit host settings,
install a plugin or add tools to the current Codex conversation.

## Choose the operation by what you need now

| Need | Call | Effect |
| --- | --- | --- |
| Start the configured private allocation | `native_start` (managed mode) | Starts once; later calls follow the same owner |
| Reread a known source image | `native_observe(stage)` | Historical evidence only, no new capture |
| Get a new image without keyboard/mouse input | `native_submit(stage, {source_sequence, interaction:"observe"})` | One read-only current-window review/capture; consumes a stage |
| Act on a viewed image | `native_submit` with an explicit click/keyboard decision | Existing source guards and input admission apply |
| Recover a pending committed response | `native_resume(stage, decision_sha256)` | Reads the exact request; never republishes input |
| End after reviewing the result | `native_submit(stage, {source_sequence, finish:true})` | Evaluates and cleans up without more input |

For fresh observation, include only `source_sequence` and `interaction` in the
decision. Point, tail, finish flags and extension fields are rejected, even if
empty or false. The source sequence comes from the last image you viewed and the
stage from its valid continuation. Current-window review can follow focus back
from a closed dialog on the private display; it never moves focus and revokes
old target aliases. A capture is not a readiness or success assertion. Failure
does not permit replay. Leave stage capacity for later input and explicit finish.

After Save, inspect the returned image. If a dialog is still being painted,
request a fresh observation instead of guessing a button or sending a dummy key.
After confirming the visible format choice, inspect the sheet before finish if
visual completion matters. `finish_after` closes the session after the action;
it cannot leave the same session available for another visual check afterward.

The [Calc visual-finish record](../../runtime/results/native-calc-visual-finish-01/README.md)
contains this exact pattern with two input programs and two explicit observations.
It used seven MCP calls including startup, explicit finish and process status;
it is correctness/recovery evidence, not a speedup. The earlier
[wait-only keyboard failure](../../runtime/results/native-snapshot-calc-transfer-01/README.md)
shows why wait_update alone is not a supported keyboard continuation.
The MCP adapter now rejects an empty, wait-only or observation-only keyboard
tail before publishing a request: keyboard actions must contain `text` or
`key_chord`. Protocol tests verify that these refusals leave the request slot
unused and the retained image readable, then allow a valid submission. This
early input-presence check does not certify the remaining tail or runtime
admission rules. It is not evidence of a new live GUI recovery trial.

- `native_observe(stage)` reads the retained source image, without recapture.
  It includes `session_context` containing the recorded public goal and exchange
  contract, with exact source hashes. Missing or malformed context stays explicit
  and does not erase a valid image. No evaluator output is read. Context describes
  the task; it grants no authority and is not an atomic snapshot with the image.
- `native_submit(stage, decision, timeout=5)` uses existing immutable publication
  and guarded action execution. After pending/error, never retry submit.
  The tool schema describes source_sequence, point, expected_title, interaction,
  tail and strict boolean finish/finish_after. Action decisions need point/title;
  finish=true needs only source_sequence; interaction=observe needs only
  source_sequence and interaction. Malformed envelopes refuse before
  publication. Unspecified defaults are not inserted into the saved request;
  extension fields remain available for action decisions. Tail/runtime admission is still checked
  by the existing harness and backend, not certified by this input schema.
- `native_resume(stage, decision_sha256, timeout=5)` follows the existing
  read-only digest-bound path. It does not create a missing request.

The run is bound at server startup; tools cannot select another filesystem path.
Calls are serialized. Existing source, request, reply and image checks remain.
Completed exchange responses include descriptive `continuation` metadata.
At a boundary, `source_available` supplies the explicit next stage,
source_sequence and source-file SHA256 only if the retained next source matches
the returned observation and its image is available. It is a snapshot, not
authority or proof that an application is still ready. Continue choosing actions
from the image; ordinary source binding and admission still apply.
An occupied next request returns `already_submitted`; inspect/resume that request
instead of sending it again. Missing/mismatched images or sources and exhausted
stage bounds return `needs_review`. Non-boundary responses provide no next-stage
advice. The metadata does not discover arbitrary stages or replay input.
SDK/process errors or transport cancellation do not prove an action was absent;
reconcile the selected request/reply. This adapter grants no extra authority.
Attach mode does not allocate GUI sessions. Neither mode infers next stages,
installs sensors or chooses actions. Harness timeouts and cleanup remain the
harness's concern.

## Managed startup

Managed startup accepts `--text-gap-ms 0|2|10`, forwarding the existing research
harness pacing policy. Default remains 0. For an explicitly paced Calc run add
`--text-gap-ms 2`; allocation metadata reports the selected value and launch.json
records it in the child argv. This is a launch-time choice, not a dynamic setting
or automatic correction. Attach mode rejects it because the existing harness's
policy cannot be changed by attaching another client.

The [earlier Calc text experiment](../../runtime/results/native-calc-text-01/README.md)
observed intermittent loss at zero gap and scoped success with explicit pacing.
Managed startup previously omitted this option, preventing that policy from
being selected through MCP. Passing it through closes that integration gap;
it does not establish the cause of repeated-character loss or a universally
safe delay. The harness still expands pacing into ordinary text/wait operations
subject to existing admission and operation limits.

For one new private Linux allocation, configure a fresh allocation directory
whose parent exists and a Python interpreter with the harness dependencies:

```sh
PYTHONPATH=.:research/live_control /tmp/agent-interface-mcp-venv/bin/python research/live_control/native_mcp_v1.py --allocation-directory /absolute/fresh-allocation --app inkscape --seed 991117 --max-stages 2 --harness-python /usr/bin/python3
```

This adds `native_start(timeout=5)` and read-only `native_status()`. Nothing is
launched until native_start. A startup timeout returns `starting`; calling start
again waits for the same process, never launches another. `ready` returns the
initial stage-1 image and public task context. It does not refresh that image or
select the latest stage: use native_observe with an explicit later stage.

Use native_submit with finish_after for the final action, or finish for an
explicit no-action finish. Then inspect the task result and cleanup receipt;
managed submit/resume responses also contain a read-time allocation snapshot.
If that snapshot is not terminal and process exit needs confirmation, use
native_status on the same owner. No waiting for exit or restart is hidden in the
snapshot. `initial_source_stage` in an action response describes startup, while
`continuation.stage` describes the next available stage; they are not substitutes.
Exit code zero alone is
not task success or verified cleanup. Managed submission requires this server
to own a live ready allocation.

An existing allocation directory, failed launch or terminal process cannot be
restarted through this server. After server restart, reconcile the retained
evidence and deliberately use attach mode with `--run-directory /absolute/fresh-allocation/run`
if appropriate. Disconnect/cancellation does not kill the child, and crash
recovery/cooperative cancellation are not implemented. The existing harness
decision timeout remains in force; this is not a guarantee of cleanup after a
crash. One server owns at most one allocation.

The [managed startup live record](../../runtime/results/native-mcp-managed-01/README.md)
contains one persistent SDK connection from startup through Inkscape save and
process exit. The local suite passed 44 tests, including failed-start refusal
and no relaunch. Host registration and performance measurements remain open.

Validation:37 local tests passed including an actual MCP stdio subprocess with
an inert file-exchange fixture. Tool discovery, separate image block, pending,
duplicate submit rejection, wrong digest, read-only final response, false task
score and unchanged request bytes/mtime were checked. This is protocol and
composition evidence, not primary-model live GUI use through registered MCP tools.
The existing CLI has real GUI evidence; that does not automatically transfer a
model usability, throughput, latency, token or cost result to MCP.

Subsequent [primary-assistant live MCP composition](../../runtime/results/native-mcp-live-01/README.md)
does operate Inkscape using the image returned by native_observe and an explicit
native_submit decision, with saved-file scoring and image/receipt audit. It uses
an SDK bridge launched through shell tools, not host-registered MCP tools. This
closes real GUI composition only; host integration and performance remain open.

The official [Python SDK v1 documentation](https://py.sdk.modelcontextprotocol.io/v1/)
documents FastMCP and stdio. This construction pins the tested maintenance-line
SDK mcp1.30.0; transitive packages are not fully locked. Runtime core has no new
mandatory dependency. A dedicated CI workflow tests only this optional adapter.
Next gate: primary-assistant use through a host-registered tool on the same
task/environment, with full content/image preservation and measured host costs.

The [Windows-to-WSL host connection record](native_host_registration_v1/README.md)
now verifies initialization, five-tool discovery and not_started status through
the Windows MCP SDK. A project-scoped Codex configuration was recognized from
its project root, but the active primary-assistant tool inventory still did not
contain these tools. This is registration/transport evidence, not direct model
use. A nested separate Git worktree did not see that project-root entry.

The [call-boundary accounting](native_call_boundaries_v1/README.md) measured
109.085 seconds overall with 4.674 seconds in SDK calls and 104.411 seconds
between calls for one Calc session. Gaps include orchestration, image handling,
deliberation and commentary; they are not model inference time alone. Do not
attribute them to the configured feedback timeout or claim host latency/token
savings before directly measuring those boundaries. Historical test counts below
and above belong to their named trials, not a single current full-suite total.

A [direct image-forwarding trial](../../runtime/results/native-mcp-direct-image-01/README.md)
passes the actual MCP text/image blocks through orchestration without a separate
view_image call. Primary use saved the expected Inkscape geometry and retained
the full responses. This removes two explicit view calls in that run, not the
shell/SDK bridge or decision-file boundary. It is an interim composition recipe,
not automatic host registration or demonstrated latency/token savings. Preserve
complete JSON output; truncation or split chunks must never trigger action replay.
