# Native Codex app-server initialization

The grounding adapter can now launch a direct Codex executable instead of requiring Node plus a JavaScript CLI path. The direct command shares the existing feature and configured-MCP restrictions with the Node command. Callers may still use the original interface; injected test clients do not launch a server.

A WSL Ubuntu process started the installed Windows Codex CLI 0.166.0-alpha.5.1 via interop, sent the existing app-server initialize request and closed it successfully. No thread or model call was created; existing authentication remained in place and no credential was copied into the trial or repository. Nine targeted command and adapter tests passed in normal and optimized Python. Raw status and the frozen probe are retained; they do not establish thread/turn compatibility, model usage accounting or a container-to-host connection.
