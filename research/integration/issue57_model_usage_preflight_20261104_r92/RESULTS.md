# R92-A01 result and MCP-isolation follow-up

## One-shot preflight outcome

R92-A01 is `FAIL_OR_UNKNOWN`. The host worker initialized App Server and created a read-only ephemeral thread, then refused before `turn/start` because two MCP servers were not disabled. The retained `mcpServerStatus/list` reply reported `codex_apps` as `starting` (2,262 tools) and `cua_repl` as `connected` (3 tools). `turn/start` count was 0, `turn/completed` count was 0, and no token-usage event or structured answer exists. No MCP tool was called, no UI input was sent, and no Calc task action occurred. The attempt is consumed and was not retried.

The R92 `audit.json` and worker receipt preserve the terminal classification. The raw protocol journal and full response are retained under `r92-a01/spool/protocol.jsonl`; raw data is local evidence and is not staged for publication because it contains the connected app/tool catalog.

## Bounded command-free remediation check

A fresh App Server process was launched with the existing `research/live_control/codex_app_server_command_v1.py:direct_command` builder. It created one ephemeral read-only thread and queried MCP status; it never sent `turn/start`. The complete status response listed `node_repl` and `openaiDeveloperDocs`, both explicitly `disabled` with zero tools. No plugin-injected `codex_apps` or `cua_repl` entries appeared. The retained diagnostic journal and audit are under `mcp-isolation-diagnostic-01/`; audit passed with zero model turns.

## Code repair

The spool worker's own `command()` helper previously disabled feature families but did not disable names present in the user's Codex config. It now reads only the configured MCP names and passes `enabled=false` overrides for those existing entries. It does not expose config values or invent names. Quoted names are escaped as TOML keys. Existing worker status inspection remains fail-closed. A caller must use this helper; R92-A01's preregistered caller deliberately used a bare command and remains unchanged in the frozen record.

Local verification: `py -3.13 -m unittest test_app_server_spool_worker_v1 test_codex_app_server_command_v1` — 9 passed. The first test launch lacked the two test directories on `PYTHONPATH`; the corrected invocation is the passing result above.

## Scope

This closes the setup-isolation defect demonstrated by R92 and verifies a no-turn isolation path. It does not establish provider token accounting, task effect, latency savings, or a successful live control comparison. A future provider attempt requires a new preregistration and must pass the disabled-server gate before its one model turn.
