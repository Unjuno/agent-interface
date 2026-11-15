# Current-main Win32 orphan-recovery verification (2026-11-15)

## Fixed source and environment

- Repository: `Unjuno/agent-interface`
- Main baseline: `fc15701d25427f74e96ca5ac97fa06685a1182de`; the pending-result regression is the candidate test added on this branch
- Runtime: CPython 3.11.9 on the attached Windows host
- No native input, Docker/WSLc command, or replay of R269 was performed.

## Commands and outcomes

| Mode | Command | Result | Raw log SHA-256 |
| --- | --- | --- | --- |
| Normal | `python -m unittest runtime.guarded_win32_v1.test_process_cancellation runtime.cli_v1.test_win32_supervisor_helpers` | 74/74 PASS | `9423EE390CA7E2E192F85FAFACBC72927355C945D334AD2E285E81C2159A7593` |
| Optimized | `python -O -m unittest runtime.guarded_win32_v1.test_process_cancellation runtime.cli_v1.test_win32_supervisor_helpers` | 74/74 PASS | `3156CD8B4D1A45D1B03BDAFED593C73D5B4918D6ED7BDFDD0E856710C8733711` |
| Normal | `python -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_stdio_exception_unknown_then_fresh_generation_recovery` | 1/1 PASS | `2D90B7ED67DA212EDF687E16D557A2EF6010ED8501EB6CF99D36409D492623C5` |
| Optimized | `python -O -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_stdio_exception_unknown_then_fresh_generation_recovery` | 1/1 PASS | `3F1A5656E2A16C83197EACBB92184E68D703C4CA42E80567504DC86681672994` |

The public MCP case verifies the source action stays UNKNOWN and unreplayed, the separately bounded recovery is queried under a fresh target generation, and a later task attempt is distinct and bound to its own call ID. These are protocol/helper results, not native GUI recovery, MAP01 task success, or #57 efficiency evidence.

## Delayed recovery-result query regression (candidate)

The test delays a fake supervisor beyond the public tool's fixed six-second response wait, returns a typed UNKNOWN receipt, then reads that exact `call_id` through `interface_results`. It asserts no replay and exactly one recovery invocation. It uses no native input and does not qualify real-backend timing.

| Mode | Command | Result | Raw log SHA-256 |
| --- | --- | --- | --- |
| Normal | `python -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_pending_result_is_queryable` | 1/1 PASS (8.855 s) | `4350A56F6F20F96F3420B64648898BB3262839811B4504389D746110A254BC50` |
| Optimized | `python -O -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_pending_result_is_queryable` | 1/1 PASS (7.547 s) | `92B023F0BD05F3306DCEABF7207ABA8CBA28841132F5CDF5208BEC2BAD7A9418` |
## Orphan-recovery public API branch matrix

The success, pending-result query, refusal, and UNKNOWN public recovery paths were run together on main baseline `fc15701d25427f74e96ca5ac97fa06685a1182de` plus the candidate pending-query regression. The pending path delays only a fake supervisor; no live input was issued.

| Mode | Command | Result | Raw log SHA-256 |
| --- | --- | --- | --- |
| Normal | `python -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_tool_is_bounded_and_keeps_source_unknown runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_pending_result_is_queryable runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_refusal_is_an_mcp_error runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_unknown_is_an_mcp_error` | 4/4 PASS (9.374 s) | `303EE1A4A6F4A07495A1A798A5D40932479239C48BC278BD91739DC45893E502` |
| Optimized | `python -O -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_tool_is_bounded_and_keeps_source_unknown runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_pending_result_is_queryable runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_refusal_is_an_mcp_error runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_orphan_recovery_unknown_is_an_mcp_error` | 4/4 PASS (8.227 s) | `528D35E1CE55C5BC5FF93B923EC01CD8C950F177BF016AE841AE023450945FF2` |
