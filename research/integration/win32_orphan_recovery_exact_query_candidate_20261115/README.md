# Exact orphan-recovery result query candidate (2026-11-15)

## Scope

On candidate base `a2ccc3a8df2ba7753e439f9c8457b79f32f7a1cc` (branch `candidate/pr10303-current-main-reconcile-20261115`), add exact-call retrieval coverage for a successful orphan-recovery control receipt that completes after the public tool's 6 s response wait. The regression checks UNKNOWN source-action preservation, verified recovery release and 2 s horizon fields, `task_success=null`, replay denial, fresh-generation requirement, and exactly one supervisor invocation. Delayed UNKNOWN and immediate UNKNOWN results remain covered alongside it.

The live R269 source was not replayed. No native input, game interaction, Docker, or WSLc operation was part of these tests. This is Fake-backed protocol integration evidence only.

## Change

- `runtime/cli_v1/mcp_server.py` now sends retained `recover_orphaned_input` reports through the management/control receipt path in `interface_results(call_id)`. This preserves recovery status and release fields rather than wrapping the control receipt as a generic image review.
- `runtime/cli_v1/test_mcp_supervised_win32.py` adds a delayed-success exact-call query regression. Its 2 s horizon fixture is internally consistent: 21 observations span 2 s with a maximum sample gap of 100 ms.
- `docs/CURRENT_GOAL.md` records the candidate-only result and limitations.

## Reproduction

Environment: Python 3.11.9, Microsoft Windows 11 Pro, Windows PowerShell, local candidate worktree. No provider/model call or live GUI was involved.

~~~powershell
python -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_late_success_result_is_queryable_once runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_pending_result_is_queryable runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_unknown_is_an_mcp_error
python -O -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_late_success_result_is_queryable_once runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_pending_result_is_queryable runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_unknown_is_an_mcp_error
git diff --check
~~~

Results: 3/3 passed normally (15.054 s) and 3/3 passed under `-O` (13.829 s). Captured output: `normal.log` and `optimized.log`.

## SHA-256

- `normal.log`: `33E611C4EB704DA9869788E4098A3C693379409169852CD21ADB2DCE92426929`
- `optimized.log`: `99645057063B8E94442691B09CFAAEA7C1DDCC981A823009A57D1C7FCDA25751`
- `runtime/cli_v1/mcp_server.py`: `B9616D40A9D559F9A7477CC9DB070C5C9009BE95B9E6CB6B95D40AC95F45376E`
- `runtime/cli_v1/test_mcp_supervised_win32.py`: `5633344567D741FE33F39A63BE51B1872B592CCE894F02E57E51D290F0CB25E9`
- `docs/CURRENT_GOAL.md`: `0DFEE20AC246821A7DF70732B262DD5A752D6F92209391EC7FC8AB52E53781AE`

Candidate changes have not been pushed or merged to main. The broader candidate suite has the previously recorded intermittent failures; this focused check does not clear that status, establish native recovery, or prove MAP01 effect.
