# Recovery status — allocation 03

This archival package preserves the frozen runner/auditor variants and
`STOP03.md`. The allocation stopped before MCP initialization or GUI input:
the adapter requested `runner_effect_v2.execute_mcp`, but the frozen parent
exposes `execute_mcp_v2` and installs it only inside `main()`.

The one recorded call ended as `STOP_OR_FAIL_CALLER`; formal/task rows: 0;
model/network/input: 0/0/0; retries: 0. This is an execution STOP, not a
scientific FAIL. Allocations 01, 02, and 04 remain distinct. No formal rerun or
new Docker experiment was made during this archival recovery.
