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

- `native_observe(stage)` reads the retained source image, without recapture.
  It includes `session_context` containing the recorded public goal and exchange
  contract, with exact source hashes. Missing or malformed context stays explicit
  and does not erase a valid image. No evaluator output is read. Context describes
  the task; it grants no authority and is not an atomic snapshot with the image.
- `native_submit(stage, decision, timeout=5)` uses existing immutable publication
  and guarded action execution. After pending/error, never retry submit.
  The tool schema describes source_sequence, point, expected_title, interaction,
  tail and strict boolean finish/finish_after. Action decisions need point/title;
  finish=true needs only source_sequence. Malformed envelopes refuse before
  publication. Unspecified defaults are not inserted into the saved request;
  extension fields remain available. Tail/runtime admission is still checked
  by the existing harness and backend, not certified by this input schema.
- `native_resume(stage, decision_sha256, timeout=5)` follows the existing
  read-only digest-bound path. It does not create a missing request.

The run is bound at server startup; tools cannot select another filesystem path.
Calls are serialized. Existing source, request, reply and image checks remain.
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
native_status separately reports process termination. Exit code zero alone is
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

A [direct image-forwarding trial](../../runtime/results/native-mcp-direct-image-01/README.md)
passes the actual MCP text/image blocks through orchestration without a separate
view_image call. Primary use saved the expected Inkscape geometry and retained
the full responses. This removes two explicit view calls in that run, not the
shell/SDK bridge or decision-file boundary. It is an interim composition recipe,
not automatic host registration or demonstrated latency/token savings. Preserve
complete JSON output; truncation or split chunks must never trigger action replay.


## Returned continuation reference

At a completed stage boundary, `native_submit` and read-only `native_resume`
include `continuation`. `source_available` carries the next stage, source
sequence and exact source-file SHA-256 only after the retained next observation
matches the delivered image identity. `already_submitted` means the next request
slot is occupied; inspect that request rather than submitting again.
`needs_review` reports missing/conflicting image/source or exhausted stage bounds;
terminal responses return unavailable. These are facts at read time, with
`authority: none`, not scheduling instructions, new input permission or task
success. Existing source/admission checks still govern the next primary decision.
The server does not author or send it. No pending request is automatically replayed.

## Managed process snapshot

Managed `native_submit` and read-only `native_resume` responses include an
`allocation` snapshot alongside the action receipt and image. A terminal process
with an available exit code may make a separate `native_status` call unnecessary.
A still-live process requires later status reconciliation; no completion is
inferred. The original startup source is named `initial_source_stage` here so it
cannot be mistaken for the next continuation stage.

Snapshot failures return `allocation.status: needs_review` while retaining the
action outcome and image. If the process exits between its first nonblocking poll
and the owner-state read, status polls once more without waiting. Exit status does
not establish task success or verified cleanup. This adds no background sensor,
restart, input replay or automatic next decision. Attach-only responses do not
include a managed allocation snapshot.

## Request validation

`native_start`, `native_submit` and `native_resume` accept only numeric wait
seconds in 0..30. Strings, booleans and out-of-range values are rejected before
allocation or request publication. Zero performs a nonblocking poll.
A finish-only decision contains exactly `source_sequence` and `finish: true`.
Additional fields, even empty/default-valued action fields, are rejected so an
intended action cannot be silently ignored. Use `finish_after` with an explicit
action when both action and termination are intended.
