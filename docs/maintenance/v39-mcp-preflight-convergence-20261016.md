# V39 MCP preflight convergence

2026-10-16. Local construction checks only; no Codex, MCP server, model, game,
WSL or live input was launched.

## Source and adoption

[PR #8839](https://github.com/Unjuno/agent-interface/pull/8839), exact head
`cf399788e32d1430fa233c7ac41deb83a2711d67`, proposed configured-name discovery
through `codex mcp list --json`, a fixed disable-list intersection and bounded
pre-start failure receipts. Its original commits/tests remain in GitHub history.

Main base `3f33f885af6c4047bb5dc48a2269a5c9f1b129d7` already includes
[PR #8837](https://github.com/Unjuno/agent-interface/pull/8837), including
`3203a7fcf93115d36ded866fb087b7e28707860f`: direct local configuration reading
and individual disables for every configured MCP, plus the current Windows/WSL
executable selection. Replacing this with the old PR would lose later work.

The remaining failure-custody requirement is carried into the current launcher:

- A missing profile remains valid. Existing unreadable, malformed or invalid
  server-table configuration refuses command construction before client creation.
- Server names are quoted as literal TOML keys, including dots, quotes and
  Unicode. The fixed historical server-name list is not restored.
- `main()` writes `mcp-preflight-failure.json` with fixed stage/reason, exception
  class and failed status. It excludes configuration, exception text and output.
  A secondary receipt-write failure adds only its class to the original error;
  the original exception is re-raised. No CLI listing subprocess is introduced.
- The cover-terminal main fixture explicitly substitutes command construction,
  and accepts the current `terminal_predicate` source-refresh keyword. Its
  terminal/release assertions remain intact. Dedicated preflight tests execute
  the real command builder and actual `main()` failure boundary.

The old CLI-list parser, five-second listing timeout and old executable override
are specific to the displaced listing design; they are not required or claimed
as adopted. This change does not measure or bound local file-read latency.

## Executed checks and limits

New first RED: four test methods, six assertion failures and three errors,
including subcases. This exposes silent configuration fallback, incorrect dotted
key interpretation and missing failure receipts. The final five methods also
check actual malformed-configuration `main()` refuses before any client/process.

First broad run: 68 tests, 37 errors and one skip in both normal and optimized
Python. All 37 errors came from the existing cover-terminal substitute rejecting
`terminal_predicate`; the same lambda is present in the base. After its minimal
signature repair, both modes pass 68 tests with one skip. The skipped optional
real Codex handshake was deliberately disabled by clearing executable-discovery
environment variables in the external runner.

Runner and original logs are retained on the working host under
`outputs/repository-consolidation-20261015/test_mcp_preflight_integration.py`,
`mcp-preflight-red-first.log`, `mcp-preflight-*-first.log` and
`mcp-preflight-*-fixture-repair.log` in the `new-chat-2` workspace. They are local
test receipts, not publicly archived experiment raw or a fresh live allocation.

This resolves startup configuration/failure custody only. Local configuration
is a snapshot: later changes, effective configuration outside this file,
server acceptance, release timing, GUI/task correctness and efficiency remain
outside the result. Keep the scientific parent Issues open.
