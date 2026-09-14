# Frozen command-free app-server startup comparison

This preregistered comparison started six fresh app-server processes in a
fixed alternating order.  Each process initialized the protocol, created one
ephemeral Luna thread, observed startup notifications for 500 ms, and exited.
No model turn was started.

The baseline thread-start measurements were 522.660, 176.169, and 211.395 ms
(median 211.395 ms).  The capability-minimized measurements were 94.368,
104.831, and 85.609 ms (median 94.368 ms).  The observed median difference was
117.027 ms.  All baseline runs emitted nine MCP startup notifications; all
minimal runs emitted zero.

The minimal command disables apps, plugins, browser/computer-use features and
the five configured top-level MCP servers.  It is suitable only for a planner
whose observation arrives as text and a local image and whose answer is
returned through the app-server protocol.  A later controller must enable any
capability that it actually asks the planner to use.

Two failed discovery conditions are retained because they narrow the result:

- `-c mcp_servers={}` did not clear configured servers.  This matches the
  behavior recorded in [openai/codex#16045](https://github.com/openai/codex/issues/16045);
  individual `mcp_servers.<name>.enabled=false` overrides were required.
- Disabling only the visible top-level servers left plugin-injected capability
  configuration active and app-server startup failed with an unrelated
  `invalid transport in mcp_servers.blender` diagnostic.  Disabling the plugin
  and app feature families as well produced the measured zero-notification
  condition.

This result supports removing avoidable fresh-process capability startup from
the persistent planner path.  It does not show faster model inference or lower
token use, and three samples per arm do not characterize the full latency
distribution.  The next gate is a persistent adapter with deterministic tests
for completion, interruption, late notification, and completion/interrupt
races before any live controller integration.
