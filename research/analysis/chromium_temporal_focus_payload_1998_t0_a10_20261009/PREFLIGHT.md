# A10 preflight

The formal input run was not started during preflight.

- Docker context: `orbstack`, endpoint `unix:///Users/taka/.orbstack/run/docker.sock`.
- OrbStack server: 29.4.0, Linux/arm64. `docker info` succeeded.
- Global `docker image ls` failed while reading an unrelated containerd content blob. This was not retried. The exact Node image digest below was independently inspectable and runnable without a pull.
- Exact Node image: `node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`, image ID `sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`, Linux/arm64.
- Bounded preflight smoke mounted the source-frame directory read-only, disabled networking, used a read-only root, 1 CPU, 256 MiB memory, 32 PIDs, and UID/GID 1000:1000. It printed Node `v26.10.0` and read one pinned source PNG size as 26,601 bytes. It did not invoke the A10 candidate or produce a crop result.
- No running Docker containers were present at preflight.
- Available filesystem space was 128 GiB; expected A10 output is limited to three small crop PNGs and bounded JSON receipts. No images or other shared data were removed.

The exact preflight command and result are retained in `preflight/container_smoke.json`.

Construction-only test history is retained under `construction/`. Attempt 1 used a 5×4 fixture and initially asserted that the crop payload must save bytes; it instead measured −65 bytes because focus metadata outweighed the tiny crop. That invalid construction assertion was removed. Attempt 2 passed exact PNG/filter reconstruction. Attempts 3 and 4 added and verified a separate Python raw auditor and six mutation checks; attempt 4 used the exact construction-test source later frozen. None of these runs read a frozen Chromium input or invoked the formal candidate allocation.
