# Integration status - Issue #3711 short-write construction

Checked 2026-09-21 JST. `PROTOCOL.md` is frozen historical evidence; its original status line is unchanged.

## Frozen source and implementation relationship

The protocol pins these Git blobs:
- `runtime/cli_v1/__main__.py`: `871600960dfb4404f3455d2df6b3d8686cf0cac9`
- `runtime/cli_v1/test_attempt.py`: `cbc9d0c17ca3a4391593dcea00901083ceacffcb`
- `runtime/cli_v1/attempt.py`: `de8041869d216014afe3322379fa2ce080367411`

PR #3727 was based on `12f838151cc210c277e585f5c2fc8b837dedc55c`, where those same paths have blobs `a3dd52836bbfe1492c4b7ad5650ab1a58603c7e5`, `1fa20d0d757a4cb860231317ca5333600e4882cc`, and `70cc62b450c8b9c8aaa0db49b1e116388368fe4c`. Therefore #3727/#3729 are implementation successors on a different source baseline, not an execution of the exact frozen source. No exact-source construction PASS is established.

## Terminal CI outcome

The required Runtime CLI workflow on the original candidate PR #3726 reached a terminal result:
- Ubuntu run [35526981161](https://github.com/Unjuno/agent-interface/actions/runs/35526981161) ran 87 tests and ended with 3 errors in the pre-existing Linux selector test. Each error was `AttributeError: module 'runtime.backends' has no attribute 'x11_v1'`.
- The focused `test_short_stdout_write_fails_once_and_keeps_retained_report` passed in that same Ubuntu log. Windows and macOS passed; the required all-platform gate did not.
- Later #3727 and #3729 Ubuntu jobs also ended with selector import errors. They do not repair the frozen-source mismatch.

Classify this allocation as `STOP_CI_INFRASTRUCTURE` with an independent source-identity STOP, not HOLD or `INCOMPLETE_CROSS_PLATFORM_CI`: the workflow is terminal, the focused assertion is not reported failed, and the candidate source differs from the frozen target. Do not retry or relabel later-source checks as exact-source validation.

## Scope limits

This is a mocked short-write construction case, not an induced OS pipe truncation or live consumer disconnect. The actual closed-pipe case is separately covered by merged PR #3723. Issue #3711 remains open for its other gates. No local Docker, GUI, model, native input, or live-application allocation is claimed.