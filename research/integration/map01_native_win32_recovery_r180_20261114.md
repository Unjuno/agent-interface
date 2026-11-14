# MAP01 native Win32 recovery R180 (2026-11-14)

## Disposition

`PARTIAL_EVIDENCE_STRICT_RUNNER_GATE_STOP`. R180 used current main `5fc76d9f759ec9b9331bd43716a555f25276243e`, accepted exactly one native `LEFTDOWN`, then the isolated producer exited with code 86. The public source action remained `unknown`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`; its separate cancellation record reported `recovered`, confirmed release, and replay denied.

The runtime recovery contract itself is verified from the retained owner receipt. Its bounded `button_up` attempt shows `SendInput` started, returned count 1, and returned without error. The receipt has 77 neutral observations, 32 ms maximum sample gap (100 ms allowed), first observation 16 ms after release receipt, and final observation exactly 2 seconds after release receipt. `late_input_validation_error` is null. The injected producer exception to release receipt was 15 ms (750 ms bound). An independent post-stop same-generation neutral horizon also verified 2 seconds (180 samples; 12.0668 ms maximum gap).

The frozen private runner stopped before completing its own primary-endpoint audit because it required `late_input_horizon_verified == true`. That property is not present in the public cancellation result; the result exposes the timestamps, count, gap, owner status, and validation error. The runner therefore reported `automatic recovery two-second horizon failed` even though the retained owner result is `recovered` and the underlying horizon checks pass. This is a runner/public-result projection defect. The attempt is kept **partial**, not promoted to an overall preregistered PASS, because the orchestration runner exited before its remaining checks.

## Effect and cleanup evidence

The before and post-recovery full-resolution images were classified by the frozen multiclass HUD oracle as 50 and 49, respectively. The post-recovery capture is bound to PID 2676, HWND 42208518, and the same target generation; foreground HWND matched before and after capture. This verifies the expected observed one-round effect, but does not establish task success (`null`). After the saved effect capture, a separate CUA close-coordinate attempt left the visible HUD at 48; this later UI event is recorded separately and excluded from the R180 before/after pair. The owned target was then closed by the identity-checked bounded WM_CLOSE path, without forced termination; passive process lookup confirmed it absent.

## Frozen source, evidence, and limits

- Frozen conditions: `conditions-r180-final.json`; source tree `ad28bdafe5db374f43d66e4f292324e3c77063f3`.
- One accepted dispatch, one producer-only exit 86, one automatic recovery; no replay.
- `task_success` remains null. The exact effect is a verified observation, not a task-success claim.
- The separate CUA screenshot was visually inspected and its screenshot ID/ammo was recorded in the effect-capture receipt; the hash-manifested full-resolution observer capture is the durable image used by the pinned classifier.
- Raw and adjudication scripts remain local-only under `private-packets/map01_native_windows_current_main_r180_abnormal_exit_20261114/trials/r180_native_win32_automatic_completion_recovery_map01/`. The post-adjudication manifest contains 159 entries; all 159 size/SHA-256 checks passed. Manifest SHA-256: `a0209aa1cc9adb7e67e6f038cd7c2ac5c0e3dbf16f6fd3e789fa6c1d1452e371`.
- No same-condition efficiency comparison or general reliability claim is established. #57 remains open.

## Next

An offline R181 private-runner terminal-gate candidate now wires public horizon projection together with source/cancellation scopes, the button-up receipt, producer witness, and exception-to-release bound. Ten fixture tests passed under CPython 3.11.9 normally and under `-O`, including the retained R180 terminal/fault result; short horizon, excessive gap, explicit false flag, mismatched generation/scope, wrong producer exit, and excess latency fail closed. The candidate is local-only at `private-packets/map01_native_windows_current_main_r180_abnormal_exit_20261114/runner-candidates/r181-horizon-projection/`; its 20-entry manifest is verified. No live evidence or new allocation is claimed.

The offline R181 terminal-gate candidate integrates scope, release-attempt, producer-witness, latency, and horizon checks. Ten fixture tests pass under normal and optimized CPython 3.11.9. Its 20-entry manifest SHA-256 is `21479e7ce7d1d5887f00419dcef72508323f10dab727c9dfda40aab3f0e61695`. Next, wire this candidate into a complete copied runner and fixture-check every frozen gate; no live attempt is authorized or claimed here. Preserve the frozen R180 runner, conditions, and raw.

### Public cancellation projection candidate

On candidate branch `research/issue57-v3-integration-crosswalk-20261114`,
`OwnedWin32SessionOwner._refresh` now writes the bounded-horizon verdict it
already uses for custody resolution into the retained cancellation result as
`late_input_horizon_verified`. The exact `interface_results(call_id=...)`
MCP text response is covered by a regression: the v3 caller parses that exact
JSON body, but still returns uncertain when the independent recovery readback
does not bind to the horizon end. The original action stays UNKNOWN, task effect
stays unset, and replay stays denied. This is a Fake producer/supervisor result
shape check; it does not change R180's partial classification or prove a live
horizon. Owner, MCP, and compiled-caller suites pass 95/95 in normal and
optimized CPython 3.11.9. A new native attempt is still needed to validate the
projection against a current Win32 recovery receipt and complete the frozen
runner audit.
