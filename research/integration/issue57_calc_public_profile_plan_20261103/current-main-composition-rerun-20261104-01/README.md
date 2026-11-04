# Current-main public Calc composition rerun — 2026-11-04

## Result

At source commit `27c9814890ff753e632274658c35639b58ceb9e9`, the existing `test_mcp_endpoint_composition.py` module passed all 16 tests in normal mode (20.473 s) and optimized Python `-O` mode (23.187 s). Docker exited 0 in both modes.

## Conditions

- Docker Engine 29.8.1, WSL2 backend; WSL memory limit 24GB, swap 8GB, gradual reclaim.
- Pinned local image `agent-interface-xvfb-mcp:late-input-r19`, image ID `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`.
- Network disabled; 2 CPUs; 4GB memory and 4GB total memory+swap; 256 PID limit; `--rm`.
- Source mount read-only; this packet is the only read-write mount.

`conditions.json` defines the interpretation; `source-files.json` binds the test and adapter source hashes to the commit. `command.txt`, `run.sh`, `normal.log`, `optimized.log`, `docker.stdout.log`, `exit-status.json`, `docker-exit.txt`, and `runtime-after.json` retain the execution record. `SHA256SUMS.txt` hashes each packet member except itself.

## Interpretation

This verifies only the offline synthetic provider-to-public-Calc composition at the stated main revision. The provider and application are test doubles. It adds no live Calc/provider call, allocation, token accounting, integrated efficiency result, WSLc result, MAP01 result, or general reliability estimate. Issue #57 remains open.
