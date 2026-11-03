# Registered MCP argument validation preflight

Date: 2026-11-03. Offline integration follow-up on current main
`72fd6970ad6592ec60b24f1775e77a397071808b`.

## Hypothesis and implementation

FastMCP 1.30.0 wraps both argument-model validation errors and exceptions from
the registered handler in `ToolError`. Catching a Pydantic error after
`super().call_tool()` therefore cannot prove that input was not sent: a handler
may itself raise the same exception after work has begun.

Following ASTORA's advice, `PublicArgumentMCP` now prevalidates through the
registered FastMCP tool's own `pre_parse_json` and Pydantic `arg_model` before
calling the normal public `call_tool` route. Only a Pydantic `ValidationError`
from that pre-invocation stage becomes a typed `invalid_request`. Valid
arguments continue through the normal FastMCP route. The error receipt includes
only field paths and Pydantic error codes (capped at 32); it omits values,
messages and raw input. Handler-raised validation errors remain `ToolError` and
are not mislabeled as no-op refusals.

This reads FastMCP's internal registered-tool metadata because the public API
does not expose argument-model validation separately. It is tested against the
repository environment and pinned test image versions below; a FastMCP internal
API change will require adapting the adapter and tests.

## Results

- The composed provider → Relay → registered Calc path rejects a numeric
  `profile_id` and malformed SHA-256 pattern before the owner handler. The
  result is `invalid_request`, operation/input false, task success null, replay
  denied. The provider ledger retains its exact raw response and reported
  21 input / 3 output tokens.
- Nested batch argument type/length/additional-key errors are normalized before
  any bridge mint. Business-rule refusals that pass Pydantic still use the
  handler's existing refusal path.
- A handler that deliberately raises Pydantic `ValidationError` after entry is
  still surfaced as `ToolError`; it is not converted to a no-operation receipt.
- Windows Python 3.11: `runtime.cli_v1.test_mcp_guarded` passed 53/53 normally
  and with `-O`; the full provider composition module passed 16/16 in both
  modes. Commands, run output and counts are in
  `windows-final-validation-20261103.txt` and `windows-validation-20261103.txt`.
- Pinned Docker image `agent-interface-xvfb-mcp:late-input-r19`
  (`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`),
  network disabled, 4 GiB memory, 2 CPUs, 256 PIDs: guarded-MCP passed 53/53
  normal and `-O`; registered Calc composition cases and focused nested/handler
  regressions passed normal and `-O`. Exact outputs are in
  `docker-full-validation-20261103.txt`,
  `docker-final-validation-and-benchmark-20261103.txt`, and
  `docker-focused-rerun-20261103.txt`.

## Added local overhead measurement

`bench_public_argument_validation.py` compares this implementation with the
previous top-level unknown/required-key preflight, using a no-op FastMCP tool.
The pinned container ran 40 paired batches of 100 valid calls per arm after
100 warmups; order alternated per batch. Both arms made 4,101 handler calls and
returned the same value. With MCP 1.30.0 / Pydantic 2.14.1 / Python 3.11.2:

| Metric | Prior preflight | Pydantic preflight |
|---|---:|---:|
| Median per-call batch mean | 13.496 µs | 16.327 µs |
| Mean per-call batch mean | 13.691 µs | 16.452 µs |
| P95 per-call batch mean | 14.828 µs | 17.254 µs |

Median delta was +2.831 µs (+20.98%) on this deliberately tiny no-op call.
This measures only local MCP wrapper cost; it is not GUI/provider latency or
end-to-end task efficiency. The full final batch samples are retained in
`docker-final-validation-and-benchmark-20261103.txt`; the preceding successful
measurement without the final one-level-dump step remains in
`docker-benchmark-rerun1-20261103.txt` for provenance.

The first benchmark attempt failed because its harness expected a
`CallToolResult`, while FastMCP's public method returns a list of content blocks.
All test groups preceding that benchmark passed. The initial failure is
preserved in `docker-validation-and-benchmark-20261103.txt`; the harness was
corrected to validate the returned content and the rerun passed. No product
failure was hidden or overwritten.

## Decision and limits

Adopt the preflight boundary: it converts registered FastMCP argument-model
failures into a determinate no-input refusal and preserves uncertainty for
handler exceptions. The measured overhead is about two microseconds per local
no-op call in this pinned environment; broader runtime impact remains
unmeasured.

This uses the deployed FastMCP/Pydantic model, not a general JSON Schema
implementation or proof of endpoint structured-output compatibility. It is
synthetic/offline evidence: no live provider, GUI, WSLc allocation, MAP01 run,
input injection, or task-effect claim. Issue #57's matched efficiency and live
computer-control gates remain open.

`SHA256SUMS.json` covers this report, benchmark script and retained validation/
benchmark outputs.
