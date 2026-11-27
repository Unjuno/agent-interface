# Issue 57 real-provider usage preflight R93-A01

## Preregistration

R92-A01 was refused before any model turn because the caller used a bare App Server command and two MCP servers remained active. The worker command helper is now fixed to disable configured MCP names, and a separate command-free App Server diagnostic confirmed both returned servers disabled with empty tool sets.

R93-A01 asks whether this corrected worker command produces one schema-constrained image plan with complete per-turn usage, reconciled against the retained App Server protocol journal. Frozen conditions: same image, prompt, schema, `gpt-6-luna`, `medium`, and 90-second timeout as R92; one worker invocation, one model turn maximum, no retry, approval never, read-only sandbox, and all configured MCPs disabled at process startup. The attempt refuses before generation if any MCP server is active.

No MCP call, UI input, Calc launch/save, or task action is allowed. This preflight tests provider-usage reporting only; it does not claim computer-control success, task effect, latency savings, or a matched efficiency comparison.

## Stop and classification

Pass requires exactly one completed eligible turn, exactly one matching `turn/start` and `turn/completed`, all five nonnegative usage values, exact equality between terminal usage and the newest matching `thread/tokenUsage/updated` event, and a complete MCP-disabled status preflight. Any setup failure, MCP activation, malformed answer, missing/mismatched usage, timeout, or extra turn is `FAIL_OR_UNKNOWN`. This attempt may not be retried.

## Provenance

Source image is the retained R91-A01 pre-input Calc frame; its SHA and dimensions are pinned in `conditions.json`. Worker/adapter files and CLI executable are hash-pinned. The corrected caller invokes the committed worker `command()` helper. Before execution, freeze the registration packet and commit it. Afterward preserve the raw App Server journal, request, response, usage receipt, audit, and final evidence manifest.
