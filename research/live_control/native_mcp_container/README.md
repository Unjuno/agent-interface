# Native MCP container preparation — execution unverified

This recipe prepares the existing private X11 harness and optional MCP adapter
for an isolated container. It has not been built or run in this task. The active
Docker version query returned no server result; Docker processes existing is
not evidence of a functioning engine. The user instructed this task to continue
WSL integration without restarting Docker. Existing WSL results do not satisfy
the container execution gate in issue #3352.

Build from the repository root when an engine is available:

```sh
docker build -f research/live_control/native_mcp_container/Dockerfile -t agent-interface-native-mcp:local .
docker image inspect agent-interface-native-mcp:local
```

The Dockerfile-specific ignore file restricts the build context to this recipe
and the tested MCP requirements. Source code is deliberately not baked in.
The base tag and apt/transitive Python dependencies are not fully pinned: record
the built image ID/digest, installed versions and exact source commit before
claiming a reproducible run. A successful build alone is not a GUI experiment.

Configure an MCP stdio client to run the following (absolute host paths):

```sh
docker run --name ai-native-exp-01 --network none -i \
  --mount type=bind,src=/absolute/checkout,dst=/workspace,readonly \
  --mount type=bind,src=/absolute/fresh-evidence-parent,dst=/evidence \
  --shm-size=512m \
  agent-interface-native-mcp:local \
  --allocation-directory /evidence/allocation --app calc --seed 991122 \
  --max-stages 4 --text-gap-ms 2 --harness-python /usr/bin/python3
```

Do not add `-t`: terminal output corrupts image-bearing JSON in the observed
Windows PTY path. Only protocol initialization occurs on connection; the primary
agent must explicitly call native_start, inspect the returned goal/image and
choose input. The allocation path must not exist. Do not attach host DISPLAY,
Docker sockets or a user desktop; the existing harness creates private Xvfb.
The evidence parent must be writable and dedicated to this run.

Retain the container after exit to inspect its state and logs. Record image ID,
source hash, command, full MCP responses, immutable requests/replies, original
image bytes, independent saved-workbook scoring, release and cleanup evidence.
Explicitly finish and check owner/container exit; transport disconnect is not
a cleanup guarantee. Never repeat a submit to recover a missing response.
No automatic cleanup/removal command is provided because failed-run evidence
must be preserved before deciding what to remove.

H: this environment may reproduce the existing managed pacing integration.
T: pending actual image build and primary-agent GUI use.
D: preparation source only; no container trace or image digest exists yet.
C: HOLD_EXECUTION_UNVERIFIED, not a completed experiment or merge-gate PASS.
U: build compatibility, private X11 execution, image delivery, shutdown and
container-versus-WSL behavior remain unverified.
