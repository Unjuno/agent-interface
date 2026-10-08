# Task-1 endpoint preflight stop

## H/T/D/C/U

- **H:** The current-tree route shim and the merged task-1 entry gate can reach the endpoint compatibility boundary without allocating GUI/input authority.
- **T:** One fresh Docker allocation, `seed=991035`, `network=none`, image `agent-interface-golden-ipc-2705:20260920-wmctrl`, task limit 1.
- **D:** `STOP_TASK1_ENDPOINT_PREFLIGHT`. The local schema was valid, but the single endpoint compatibility call returned code 1 with no usage record. The gate refused before task execution.
- **C:** `authority=false`; GUI/input/task effects were zero; prior #2705/#2730 results were not changed; no retry was performed.
- **U:** Whether the host model IPC broker is reachable from the repaired current-main route remains unresolved.

## Evidence

- Source route: current main after the backend-boundary repairs merged in #2893 and #2899, with the historical demo shim supplied additively.
- Image: `agent-interface-golden-ipc-2705:20260920-wmctrl`.
- Schema status: `VALID`.
- Endpoint status: `PREFLIGHT_FAILED`, `returncode=1`.
- Usage: `null`; fresh usage records: `0`.
- Local raw gate report: `out9/preflight/persistent/gate/gate-report.json`.

This is an infrastructure/endpoint stop, not a route success or acceptance result.
