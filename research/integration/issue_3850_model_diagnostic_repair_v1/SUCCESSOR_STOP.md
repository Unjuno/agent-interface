# Successor allocation STOP — one invalid request, zero model turns

This execution attempt is consumed as an infrastructure/protocol STOP. Preserve all raw output and do not retry its row.

- Formal CLI requests attempted: 1 (`33463f0787ff4b59948f4c4729846d7a`).
- Completed model turns with assistant message and usage: 0.
- Valid formal rows: 0/8; seven rows never started.
- Docker runner exit 1; host broker exit 1.
- Raw JSONL records an HTTP 400 `invalid_json_schema`: `program` required `additionalProperties:false`. The preregistered prompt reached the CLI once but was rejected before model generation.
- Broker stderr includes `cloudflare-api` MCP AuthRequired and a PowerShell hot-reload warning. No MCP request was sent. No credentials/config files were read, copied, or changed.
- The runner and host both attempted to create the same result path; the Docker runner failed before producing a row receipt. The first output and IPC evidence remain in the local task workspace; response/request/broker/argv are unmodified.
- Corrected local schema SHA-256: `529FF405D4DC1B254BA2F8DDD1EF802FE62A66E7262D2A0AF47E2FE6874DC5FC`. Docker-only empty-allocation audit negative control correctly reports `STOP_OR_HOLD_AUDIT_ERRORS`, with zero rows; this is not a model result.
- CLI probes with empty input were rejected before any model turn and did not prove that configured MCP startup is disabled by a process-local override. Do not infer isolation.

Issue #3850 comment 5852735888 records the disposition. A fresh allocation must freeze the corrected strict schema, single-owner result-directory creation, verified no-tools/no-MCP CLI boundary that safely retains allowed authentication, runner/broker protocol and hashes, followed by exact GitHub read-back. If such an auth-safe boundary is unavailable, stop and ask the user rather than inspecting private authentication state or trying another unregistered route. No GitHub Actions/workflow executed the experiment.
