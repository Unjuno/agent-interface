# Native research session over MCP stdio

Optional thin adapter for an already-running private native harness. It exposes
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
- `native_submit(stage, decision, timeout=5)` uses existing immutable publication
  and guarded action execution. After pending/error, never retry submit.
- `native_resume(stage, decision_sha256, timeout=5)` follows the existing
  read-only digest-bound path. It does not create a missing request.

The run is bound at server startup; tools cannot select another filesystem path.
Calls are serialized. Existing source, request, reply and image checks remain.
SDK/process errors or transport cancellation do not prove an action was absent;
reconcile the selected request/reply. This adapter grants no extra authority.
It does not allocate/terminate GUI sessions, infer next stages, install sensors,
or choose actions. Harness timeouts and cleanup remain the harness's concern.

Validation:37 local tests passed including an actual MCP stdio subprocess with
an inert file-exchange fixture. Tool discovery, separate image block, pending,
duplicate submit rejection, wrong digest, read-only final response, false task
score and unchanged request bytes/mtime were checked. This is protocol and
composition evidence, not primary-model live GUI use through registered MCP tools.
The existing CLI has real GUI evidence; that does not automatically transfer a
model usability, throughput, latency, token or cost result to MCP.

The official [Python SDK v1 documentation](https://py.sdk.modelcontextprotocol.io/v1/)
documents FastMCP and stdio. This construction pins the tested maintenance-line
SDK mcp1.30.0; transitive packages are not fully locked. Runtime core has no new
mandatory dependency. A dedicated CI workflow tests only this optional adapter.
Next gate: primary-assistant use through a host-registered tool on the same
task/environment, with full content/image preservation and measured host costs.
