# Issue #3569 — model-visible route preflight STOP

## Decision

`STOP_CONTAINER_PREFLIGHT` for the frozen allocation, with a separate
`STOP_MODEL_ROUTE_UNAVAILABLE` at the current Codex host boundary. No nonce was
generated and no model task or route observation was called. This is not a
task-performance result and does not pass or fail any transport's semantic
correctness.

## H/T/D/C/U

- **H:** The same active model host can receive equivalent visual evidence
  through direct public API, CLI, and stdio MCP routes.
- **T:** Freeze source and run a network-disabled OrbStack construction/import
  preflight before any route or model task call; verify that the current host
  directly exposes all three route conditions before proceeding.
- **D:** The one frozen container invocation exited 1 during import with
  `ModuleNotFoundError: No module named 'runtime.cli_v1.api'`. The source mount
  was a sparse checkout that did not materialize the runtime path. The active
  Codex host exposed generic shell, CUA and GitHub MCP, but no individually
  selectable Agent Interface API/CLI/MCP task tools; exact model-build and
  host-usage receipts were also unavailable. Disposition is STOP, not PASS.
- **C:** OrbStack Docker 29.4.0, Linux/arm64, image
  `sha256:0e35cdb51a82e59d359ec09b85ce835d9217a1eab65b68ce1871c9b0a85014c9`,
  `--network none`, read-only root and source mount, isolated `/tmp`. No route
  call, model call, nonce, GUI input, authority grant or external network.
- **U:** Whether the same model host can be configured to call all three
  transports directly with observable equivalent image payloads and usage
  receipts remains unknown. Shell-mediated calls/manual image presentation
  would substitute a different model interface and are not counted.

The preregistration explicitly forbids retrying this allocation after a
container-preflight failure. Its first STOP is therefore preserved; no code or
source path was repaired and rerun under the same allocation. Prior #3548,
#3557, #3561 and #3569 evidence remains unchanged and is not pooled.

## Raw command outcome

The image inspect returned the pinned local image ID and `linux/arm64`. The
single container command was:

```sh
docker --context orbstack run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,size=64m -v "$PWD:/repo:ro" -w /repo \
  issue-3548-route-unit:20260920 python3 -c \
  'import importlib.metadata as m, sys; import runtime.cli_v1.api, runtime.cli_v1.observe, runtime.cli_v1.mcp_server; print("python="+sys.version.split()[0]); print("mcp="+m.version("mcp")); print("Pillow="+m.version("Pillow")); print("python-xlib="+m.version("python-xlib")); print("API/observe/MCP imports=PASS")'
```

It failed at the first import. Because this is the preregistered one-shot
container construction gate, it was not repeated. The route-host limitation
is separately visible in this task's configured tool surface; no task call was
attempted.

## Evidence boundary

The stop says nothing about whether the frozen task would be answered
correctly, whether the route outputs are visually equivalent, or whether one
route is faster/cheaper. The prior no-model OrbStack observation-route unit
cannot establish model-host availability. Continue only with a fresh,
separately preregistered allocation after a complete source checkout and a
host that directly exposes the same-model route conditions and usage receipts.
