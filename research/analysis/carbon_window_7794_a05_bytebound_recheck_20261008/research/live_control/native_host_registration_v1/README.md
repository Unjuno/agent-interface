# Windows host to WSL native MCP: registration preparation

The Windows-installed MCP SDK successfully initialized a stdio connection through
wsl.exe to this checkout's native_mcp_v1.py, listed all five tools, and called
native_status. Status was not_started and no allocation directory was created.
The exact command/arguments and returned state are retained in handshake.json;
handshake.py is the local test helper (run from the original checkout, with its
results-local directory available). It does not call native_start or send GUI
input. This tests the Windows-to-WSL transport, not Codex image presentation.

A project-scoped configuration was created at
`C:/Users/junny/Documents/New project/.codex/config.toml`, under the name
`agent-interface-native-research`. Global configuration was not changed.
`codex mcp get agent-interface-native-research --json` from that project root
reports enabled=true, disabled_reason=null, the tested wsl.exe argument vector,
startup timeout 30 seconds and tool timeout 45 seconds. Running the same command
from the nested separate Git worktree did not find the entry. Record this scope
difference rather than treating the first lookup failure as a server failure.

The selected allocation is fresh `results-local/native-host-direct-01`, Calc,
seed 991125, max stages 8, text gap 2 ms, system Python harness. One configured
server owns at most one allocation and never restarts an existing one. Connection
alone does not launch it. A reconnect after a launched session is not permission
to create another run; reconcile the retained allocation explicitly.

No Agent Interface tools are published in the active assistant's current tool
inventory yet. Registration, handshake and actual model-callable availability
are separate checks. A host reload/new tool discovery may be required; neither
the desktop app nor Docker was restarted. Do not claim direct primary-model use,
image presentation, lower latency, tokens/cost, or completion of issue #3370.

Configuration format reference: [official Codex MCP documentation](https://developers.openai.com/ja-JP/docs/extend/mcp).
The local CLI's mcp add/get help and actual project-root get result establish
what was tested on this host. The absolute paths are machine-specific research
configuration, not a portable installer. No plugin or sensor was installed.

## Image transport check after integration

`image_check.py` subsequently used the Windows Python MCP SDK to attach through
WSL stdio to the completed two-application run, without launching an allocation
or submitting input. `native_observe(stage=7)` returned the retained sequence-22
PNG: 58,496 bytes, exactly matching the local artifact and its recorded SHA256.
All 105 run-file hashes and mtimes were unchanged. The result is in
`image-check.json`. Its model-tool-availability flag records the primary's
separate inventory inspection; the SDK script cannot inspect Codex's tool list.

Project-root `codex mcp get` still reports the configured server enabled. The
active tool inventory still has no native_start/submit/resume tools, and the
available CLI offers no MCP reload command. Successful Windows image transport
narrows the remaining gap to host registration/discovery/presentation, but does
not prove which host condition prevents exposure. No app reload was attempted;
do not infer that restarting will necessarily fix it. The reserved managed
allocation is separate from this completed-run attachment.

## Effective configuration scope, not a trust override

CLI 0.153.4's generated protocol schema describes `config/read` with explicit
cwd and includeLayers. A short-lived local app-server process was initialized
only to read those layers; no thread, model turn, MCP allocation or input was
started. `read_effective_config.py` records only layer identities, disabledReason
and presence of the target server; unrelated settings and credentials are not
retained. The helper closes its own process, not the desktop app or its daemon.

`effective-config-layers.json` shows the parent project includes its `.codex`
layer with disabledReason=null and the target server in effective configuration.
The nested separate Git worktree includes only user/system layers and no target
server. Although the user config has no matching explicit projects trust entry,
the actual parent-layer result does not support diagnosing an untrusted-project
block. No trust setting, global MCP setting or approval policy was changed.

Official [MCP configuration documentation](https://developers.openai.com/ja-JP/docs/extend/mcp)
states that project configuration applies to trusted projects; this is why the
effective layer result matters more than assuming trust from one config key.
This check used a separate read-only CLI app-server instance, not the active
desktop host. Its success cannot establish which configuration snapshot or
working directory the active host used to publish this conversation's tools.
The model-callable tool gap therefore remains unresolved, narrowed to the host
side. Do not repeatedly add duplicate registrations or broaden trust as a guess.
