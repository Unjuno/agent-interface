# Target-generation boundary audit

## Requirement-to-evidence crosswalk

| Requirement | Evidence | Finding |
|---|---|---|
| A focused Win32 action carries the generation learned from observation | `attempt-10-real-effect-held/RESULT.json`, program source and observed generation | The live held-effect recovery attempt used one matching generation end-to-end. |
| A stale generation is refused before producer start | `runtime/cli_v1/test_mcp_supervised_win32.py::SupervisedWin32MCPTests.test_stale_target_generation_is_refused_before_producer_start` | Passed locally: `status=invalid_request`, `operation_invoked=false`, no owner operation result created. |
| Fresh/current evidence is checked at the standard runtime dispatch boundary | `runtime/cli_v1/api.py::_win32_target_generation_error`, invoked before `session.dispatch` | Current generation is read and compared before standard dispatch; the public interface call reaches this path. |
| Target-window lifetime stays bound between precheck and native input | No live or composed race evidence in this packet | **Open boundary.** Current source describes target generation as a pre-dispatch check, not an atomic window-lifetime fence (`runtime/cli_v1/mcp_server.py` tool contract). A window can theoretically be replaced after the check and before input unless a lower-level fence prevents it. |

## Local verification

`python -m unittest runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_stale_target_generation_is_refused_before_producer_start` — 1 test, OK. The transcript is `stale-generation-test.stdout.txt`.

## Next discriminating test

Using a functioning Computer Use helper and a dedicated blank Notepad window, capture its generation, close/recreate only that test window before dispatch, then submit a program bound to the old generation through the public supervised Win32 MCP caller. Require refusal before producer start, no input, no replay, and independent state readback. This tests only pre-dispatch staleness. Separately test the narrower check-to-input race if a supported synchronization seam exists; do not describe pre-dispatch rejection as an atomic lifetime fence.

This run did not execute the live stale-generation test: the Computer Use helper returned `Trusted RPC service is not configured` on initial discovery and one retry. No UI action was taken for this test.
