# Issue #3561 attempt 01 — PREFLIGHT_STOP_BEFORE_ROUTE

Container `issue3561-route-preflight-01` exited 1 in the import/version probe.
The public API and MCP modules imported successfully; the probe then accessed
`mcp.__version__`, which is not exposed by MCP SDK 1.30.0. API, CLI and MCP
observation calls: 0. Model calls: 0. Input actions: 0. This is a test-harness
error, not route unavailability or an observation result. It was not retried as
a formal route allocation. Corrected no-route preflight is separately retained
as containers `issue3561-route-preflight-02` and
`issue3561-route-preflight-03` (both exit 0).

The first formal candidate allocation `issue3561-route-unit-01` used the
runner's default 500x260 region, not the requested 320x240. It made one call
per route and passed its own audit, but is not evidence for the preregistered
320x240 condition. Preserve it under its original allocation path; do not
rewrite or pool it. The corrected, explicitly parameterized 320x240 formal
allocation is `evidence/20260920-issue3561-route-unit-02/`.
