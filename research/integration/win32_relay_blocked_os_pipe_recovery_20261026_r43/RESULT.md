# R43 OS-pipe recovery attempt

Classification: `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED`. The R42 first outcome remains immutable.

## Question

Can the standard public stdio relay route cancellation and bounded Win32 recovery while the actual child-process stdout OS pipe is full and a write is blocked?

## R43 runner change

R42's failure path tore down the relay without first sending public `interface_cancel` or reconciling exact-call `interface_results`. R43 adds one bounded cancellation attempt, drains known queued responses, polls the exact call for up to eight seconds, captures an explicit public `interface_close` response, and only then permits process teardown. It records missing/ambiguous receipts and does not replay. The source freeze includes `owned_win32_session.py`, which R42's original preregistration omitted.

## First outcome

The owned fixture and public observation preflight passed. `interface_dispatch` returned a queued call; independent native sampling did not observe SHIFT down within the 3-second pre-pressure window. The failure path sent standard public `interface_cancel`, which returned `not_cancellable`; exact-call `interface_results` returned `action.status=unknown`, `input_dispatched=false`, and a producer-start `FileExistsError`. `interface_close` returned `busy` for the unresolved operation. All raw and source hashes pass (17 raw entries, 11 pretrial entries). Fixture exited 0 and original foreground HWND was restored. No OS-pipe pressure was applied; no replay.

## Diagnosis

The error is explained by the R42-derived `relay_child.py` constructing native components before `create_server` and then ignoring the `producer_root` passed to the supervised producer factory. `NativeWin32StandardProducerFactory` therefore used `run/server` as its output root and attempted to create the same call-ID directory already owned by the MCP server request journal. It failed before starting a producer process. The next attempt must construct owner and producer components through the paired factories using the distinct `root` and `producer_root` supplied by `create_server`. R43 establishes a harness wiring defect, not an input effect, release result, or OS-pipe recovery sample.

## Status and limits

This packet is an additive successor; it does not revise R41/R42. Its relay server uses the in-process MCP adapter while the child-process stdout is a real OS pipe. It is not a production MCP subprocess transport, MAP01, WSLc, Docker, task-effect, efficiency, or reliability result.
