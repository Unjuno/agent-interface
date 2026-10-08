# Applying the existing public receipt projection consistently

At integration main `e9e0a0d85792e77822ae37258c02da325dc1b21b`, the primary
assistant noticed its recent public observations still used full receipts while
dispatch calls already used `compact=true, report_refs=true`. No new runtime
feature is needed: the existing observation tool supports the same explicit flags.

This offline recount selects all nine observe/dispatch replies from the two
frozen primary counter recovery trials, including both injected input failures.
Management replies (recovery/close) use another format and are excluded explicitly.
Original source archive hashes, member paths and byte-exact replies are retained
in inputs.json. The verifier checks them against the original frozen archives,
expands each receipt to v1, reapplies the existing v3 projection and proves exact
expansion equality. The rest of the envelope and native image blocks are unchanged.
It starts no server, capture, input, GUI or model inference.

The three originally full observations total 13,754 UTF-8 text bytes; explicit
projection would return 10,461, removing 3,293 bytes (about 23.94%). The six dispatch
replies already used this projection and are unchanged. Across all nine selected
replies the text total is 40,368 -> 37,075 bytes (about 8.16%). These are text-block
bytes using the existing MCP JSON serialization, excluding images and transport
envelopes. They are not actual model input tokens, billed cost or latency.

The full raw report remains in the same response at receipt.source.raw_report.
Only receipt.report becomes a declared local reference. No extra tool call is
needed to inspect failures or restore the full receipt. This does not summarize,
crop or omit an image, and does not grant freshness or action authority.

Decision: use the existing opt-in flags consistently for subsequent primary
public observations when the host can interpret v3 receipts. Keep full output
as the compatibility default; do not promise a universal size reduction or change
management tools to accept unsupported flags. The current interface guide now
shows the explicit invocation and same-response report location.

Run `python3 -O runtime/results/public-observation-projection-01/verify.py` to
recount the frozen result. --record only creates a missing result and refuses
to overwrite one. This verifies a use pattern on actual retained replies; it
does not constitute a new primary live task or a matched token-cost experiment.
