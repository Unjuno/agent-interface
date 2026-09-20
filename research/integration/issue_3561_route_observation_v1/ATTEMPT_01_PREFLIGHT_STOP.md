# Issue #3561 attempt 01 — PREFLIGHT_STOP_BEFORE_ROUTE

Container `issue3561-route-preflight-01` exited 1 in the import/version probe.
The public API and MCP modules imported successfully; the probe then accessed
`mcp.__version__`, which is not exposed by MCP SDK 1.30.0. API, CLI and MCP
observation calls: 0. Model calls: 0. Input actions: 0. This is a test-harness
error, not route unavailability or an observation result. It was not retried as
a formal route allocation. Corrected no-route preflight is separately retained
as container `issue3561-route-preflight-02` (exit 0).
