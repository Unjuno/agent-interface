# Registered MCP required-argument preflight

Date: 2026-11-03. Offline composition follow-up on current main
`458b18b07c54d6f35e32846ac28847d6f36df4f6`.

## H — hypothesis

When a completed object-shaped model response omits arguments required by the
registered Calc MCP tool, the public endpoint can use its own advertised
`inputSchema.required` to return a determinate no-operation refusal before
FastMCP coercion and before the owner handler. The outer provider ledger should
still retain that completed generation's exact raw response and reported usage.

## T — composed test

`test_mcp_endpoint_composition.py::test_object_output_with_incompatible_mcp_shape_is_rejected_before_owner`
passes a synthetic provider response containing `{}` through the recorded
provider caller, public Relay, actual `PublicArgumentMCP`, and the registered
Calc tool schema. The schema's required list was observed directly from
`server.list_tools()` as `profile_id`, `bindings`, `reviewed_sequence`,
`reviewed_artifact_sha256`, `blank_reviewed`, and `attempt_id`.

The public MCP boundary now checks missing required fields before calling
`super().call_tool()` and returns `invalid_request` with
`operation_invoked=false`, `input_dispatched=false`, `release_confirmed=null`,
`effect_status=unknown`, `task_success=null`, and `replay_allowed=false`. The
composed test verifies this returned error result, the exact sorted missing
field list, one completed provider attempt with 19 input / 2 output tokens, raw
response-byte preservation, one recorded Relay tool call, and no server-side
`request.json` owner record.

`runtime.cli_v1.test_mcp_guarded.GuardedMCPTests.test_unknown_top_level_arguments_never_reach_bridge`
also passes in normal and optimized mode, confirming the existing unknown-field
preflight remains active.

Validation completed on Windows Python 3.11: the registered-shape integration
test passed in normal and `-O`; the complete `runtime.cli_v1.test_mcp_guarded`
module passed 52/52 in normal and `-O`. Both focused boundary tests also passed
in normal and `-O` using cached
`agent-interface-xvfb-mcp:late-input-r19`
(`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`),
with networking disabled and 4 GiB memory / 2 CPU / 256 PID limits. No X server
was needed for this no-owner path.

Exact Windows and Docker command output is retained in
`windows-validation-20261103.txt` and `docker-validation-20261103.txt`.
`SHA256SUMS.json` covers this report and both run transcripts.

## D — decision

**PASS for missing required top-level tool arguments only.** The previous
framework exception was not proof of task execution, but the Relay classified
it as `unknown_requires_reconciliation`. The explicit server-side refusal now
preserves no-input state in a normal MCP tool response and the provider ledger
reconciles it as a returned tool result.

## C / U — limits

This does not implement full JSON Schema validation or conversion. Wrong field
types, nested structures, regex/enum/range constraints, and genuine provider
responses remain separate cases; framework errors for those may still be
uncertain. The provider is synthetic, the owner handler is not entered, and no
GUI, live provider, or allocation was used. #54 and #57 remain open; no live
efficiency, correctness, WSLc, or MAP01 claim follows.
