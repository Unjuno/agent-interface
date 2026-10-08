# Allocation 03 STOP — adapter entry-point error

Allocation `public-mcp-dispatch-stale-effect-2907-docker-20260927-03` was invoked once in local Docker Desktop after preregistration and exact-source readback. It stopped before MCP initialization or any GUI input: the adapter called `runner_effect_v2.execute_mcp`, but the frozen parent exposes `execute_mcp_v2` and installs it only inside `main()`.

- Preserved result: `STOP_OR_FAIL_CALLER`; error `AttributeError("module 'runner_effect_v2' has no attribute 'execute_mcp'")`.
- Result SHA-256: `7cfef674ac10dd2ff26510e190066ee22a1f6737e26aeb5e08b0bdf0db06fcac`.
- Model/network/input: 0/0/0; no authority; cleanup removed owned processes and X socket.

Allocation 03 is consumed; no resume or retry. The next fresh allocation will call the parent runner via its supported `main()` and add transport scope during trace serialization. This is an execution STOP under #2907, not a scientific FAIL or a new research Issue. Preserve #01–#03.