# Exact orphan-recovery result query candidate (2026-11-15)

## Scope

On candidate base `a2ccc3a8df2ba7753e439f9c8457b79f32f7a1cc` (branch `candidate/pr10303-current-main-reconcile-20261115`), verify a successful orphan-recovery receipt that completes after the public tool's 6 s response wait. The composed checks cover both direct MCP server calls and the production CLI stdio transport. They assert that the original action remains UNKNOWN; recovery release and the 2 s horizon remain visible; `task_success=null`; replay is denied; a fresh generation is required; and recovery is invoked once.

The live R269 source was not replayed. No native input, game interaction, Docker, or WSLc operation was part of these tests. This is Fake-backed protocol integration evidence only.

## Change

- `runtime/cli_v1/mcp_server.py` sends retained `recover_orphaned_input` reports through the management/control receipt path in `interface_results(call_id)`, preserving control fields instead of wrapping them as a generic image review.
- `runtime/cli_v1/mcp_supervised_stdio_test_server.py` provides a bounded test-only delay after the fake release and 2 s horizon, before returning its terminal receipt. It models delayed receipt availability, not delayed OS input.
- `runtime/cli_v1/test_mcp_supervised_win32.py` tests delayed-success, delayed-UNKNOWN and immediate-UNKNOWN query cases, plus pending-to-recovered retrieval through the production CLI stdio entrypoint. The 2 s horizon fixture uses 21 samples at up to 100 ms intervals.
- `docs/CURRENT_GOAL.md` records the candidate-only result and limitations.

## Reproduction

Environment: Python 3.11.9, Microsoft Windows 11 Pro, Windows PowerShell, local candidate worktree. No provider/model call or live GUI was involved.

~~~powershell
python -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_late_success_result_is_queryable_once runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_pending_result_is_queryable runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_unknown_is_an_mcp_error runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_production_stdio_orphan_recovery_pending_exact_query
python -O -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_late_success_result_is_queryable_once runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_pending_result_is_queryable runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_unknown_is_an_mcp_error runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_production_stdio_orphan_recovery_pending_exact_query
git diff --check
~~~

Results: 4/4 passed normally (23.530 s) and 4/4 under `-O` (23.599 s). Captured output: `normal.log` and `optimized.log`.

## SHA-256

- `normal.log`: `DA8300E0A972E482E85FDDDFCB09655BD00BE3BC3926BB43BCE7B94F5AD02406`
- `optimized.log`: `DB0F843E4336DE551205ECB062F94594EBA53CF75132DE0FCA5F1EC92CFE4D75`
- `runtime/cli_v1/mcp_server.py`: `B9616D40A9D559F9A7477CC9DB070C5C9009BE95B9E6CB6B95D40AC95F45376E`
- `runtime/cli_v1/mcp_supervised_stdio_test_server.py`: `DDED6889C81DA9596836CBE59BACA4C1425B6E252E8D63AEE7EBD44F6D082D2C`
- `runtime/cli_v1/test_mcp_supervised_win32.py`: `5913EAB3A6B94F6CF77CC143A8791158F0BDF759DD24F50DBA7F51F11443E02A`
- `docs/CURRENT_GOAL.md`: `8E26064A1D2ADEB34FA79CFEF04F269FA8AA02F5FC3E07B36D8777C654929E5A`

Candidate changes have not been pushed or merged to main. The broader candidate suite has the previously recorded intermittent failures; this focused check does not clear that status, establish native recovery, or prove MAP01 effect.

## Current candidate HEAD recheck (2026-11-15)

Re-ran the production-stdio exact-query case against candidate HEAD `5918ffcc38addc501eb5c99e4a21a48f4e58068a`, with the new cross-call isolation assertion in the working tree. Both commands passed 1/1: normal (10.027 s) and `-O` (9.678 s). The test now queries an unrelated unknown call ID while recovery is pending and asserts it receives `unknown_call` without the recovery receipt; exact query of the real call still returns the terminal recovery receipt. This checks caller/result association, not native recovery.

~~~powershell
python -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_production_stdio_orphan_recovery_pending_exact_query
python -O -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_production_stdio_orphan_recovery_pending_exact_query
~~~

Raw output and hashes: `current-head-stdio-normal.log` (`355968e1d2f89bbd8cf5746732d83962f092bf6fd9cf7525c2b67e74cbe920b1`) and `current-head-stdio-optimized.log` (`e130b782695541bd72011b978085d3974abc82a3a7a24410ebeae4d9005d4368`). Test source `runtime/cli_v1/test_mcp_supervised_win32.py`: `293b0ecaf44afe24c95f4df51957b23d1e11e2efab938c23196f1c859f40198d`.
