# Task-1 host-broker runtime startup stop

## H/T/D/C/U

- **H:** Connecting the container runner to the local host broker will pass endpoint compatibility and allow the bounded task-1 route to reach runtime startup.
- **T:** One fresh Docker allocation, seed `991036`, image `agent-interface-golden-ipc-2705:20260920-wmctrl`, `--network none`, host broker over a shared IPC volume.
- **D:** `STOP_TASK1_RUNTIME_STARTUP_NO_PRIVATE_ENDPOINT`. Endpoint compatibility passed, then the desktop runtime exited before publishing its private endpoint.
- **C:** `authority=false`; no GUI input, task effect, retry, or acceptance claim. Prior evidence remains unchanged.
- **U:** Whether the runtime private endpoint failure is caused by the container fixture startup or the historical route's launch contract remains unresolved.

## Evidence

- Endpoint status: `ENDPOINT_COMPATIBLE`.
- Usage: input `13861`, cached input `13056`, output `201`, reasoning `58`.
- Preflight schema: `VALID`.
- Runtime stop: `runtime exited before publishing its private endpoint`.
- Host broker boundary: `container-to-host-model-ipc`, authority false.

This is a bounded infrastructure/runtime stop, not a task-success or acceptance result.
