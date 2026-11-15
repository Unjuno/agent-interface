# Current-main Win32 orphan-recovery verification (2026-11-15)

## Fixed source and environment

- Repository: `Unjuno/agent-interface`
- Main revision under test: `ce9e3d825ccfb8f7f0e62538f346238a4704c6af`
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
