# Docker Codex app-server configuration preflight r04

Each case used a disposable container with network disabled, a fresh isolated HOME, and no mounts. No model call or input event occurred. The host kept stdin open for 1.2 seconds after sending initialize. Captured stdout and stderr were decoded by the host process and saved as UTF-8; the file hashes in RESULT.json and SHA256SUMS.json cover the retained files.

The config-free case returned a successful initialize response. Adding the absent-server override `-c mcp_servers.blender.enabled=false` caused `invalid transport` and exit 1 before initialization. This reproduces the old Docker STOP cause and checks the pinned CLI without credentials. It does not establish current-main source execution, game readiness, task effect, input release, or speedup.

Current code context: CURRENT_MAIN_CONTEXT.json pins main `166ed8b54613b3b9cf03e6ce0c4645d1a93b0ea7` and hashes the controller plus its app-server command tests. The Docker probe executes the pinned CLI only; it does not run the current-main controller.
