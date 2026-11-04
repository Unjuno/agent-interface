# Issue 57 real-provider usage preflight R92-A01

## Preregistration

Question: can the installed Codex App Server return one schema-constrained image plan with complete per-turn token usage, and can the existing file-spool worker retain protocol evidence that reconciles with that usage?

Frozen conditions: one turn only; model `gpt-6-luna`; reasoning effort `medium`; one retained 1280x800 Calc screenshot from r91; 90-second turn timeout; one worker invocation; no retry or replacement. Approval is `never`, thread sandbox is `read-only`, and the existing worker verifies all MCP servers are explicitly disabled before it starts the turn. The prompt asks for a plan only. No MCP call, desktop input, Calc launch, save, or other UI operation is authorized by this preflight.

The response schema requires the visible sheet/cell state, whether cells are blank, an ordered action proposal for A1=731/A2=864 and Save, confidence, and a short visual note. The model must not report task completion. The purpose is to verify a real provider-usage and protocol-custody path before integrating it into the matched lifecycle comparison; this is not itself a computer-control success or efficiency result.

## Stop and classification

One completed response with all usage fields and exact agreement between terminal `turn/completed` usage and the newest matching `thread/tokenUsage/updated` record is `PASS_PROVIDER_USAGE_SCOPED`. Missing or mismatched usage, MCP not disabled, multiple turn starts, malformed response, timeout, or setup failure is `FAIL_OR_UNKNOWN`. Every result consumes this one attempt; no retry. Any partial token usage is retained as partial and never treated as zero.

## Provenance

Source screenshot: R91-A01 retained pre-input review image, SHA-256 recorded in `conditions.json`. The worker and adapter are the existing versions under `research/integration/standard_mcp_task_ledger_57_v1/`. CLI path, version, and executable hash are frozen in the preflight record. After the sole call, retain the raw App Server JSONL journal, request/response spool, worker result, usage, audit report, and a final SHA-256 manifest.

This tests App Server usage reporting, not upstream provider wire reconciliation or hidden provider retries. It does not compare baseline versus integrated routes, verify GUI input/release/effect, establish WSLc or MAP01, or complete Issue #57.
