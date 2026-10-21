# Native WSL Xvfb blocked-release and liveness timestamp check — r01

Run ID: `native-wsl-xvfb-blocked-release-r01-20261020`  
Source commit: `108b2717289611b4be84b897b2c56ef14a3f6032`  
Test blob: `fbc9339a69996d06519d511231b4276dca60122b`

## Result

The exact standard MCP caller test passed once on a private Xvfb server in the native Ubuntu WSL distro. The raw test report and independently checked summary are `result.json` and `audit.json`; `result.observation.png` is the retained observation image. The audit script is `audit_raw.py`.

One `KeyPress(a)` reached the synthetic application and changed its independently read property to `[1]`. A delayed `KeyPress(b)` was queued on the same owner X connection, then that owner blocked in a real `python-xlib Display.sync()` response wait. Cancellation returned in **764.307 ms**, below the test's **3,000 ms** bound. The XRes observer confirmed the expected owner process was no longer present at its client resource base; the recorded query returned the observer PID because X reused the just-retired owner's resource base for that observer connection. The source guard requires the reported PID not to equal the expected owner PID, and requires the observer PID when the bases coincide.

A separate release worker completed in **438.767 ms** and an independent keymap readback showed both `a` and `b` up. At **8,505 ms** after cancel began, both remained up and no delayed `b` press was observed. The independent synthetic task oracle passed all four checks. The terminal owner liveness timestamp preceded cancellation return by **512.471 ms**, so the snapshot was correctly treated as stale relative to that return; the terminal owner snapshot reported `alive=false`. The terminal response returned in **8.605 ms**.

The caller deliberately retained `cancel_unconfirmed`, `release_confirmed=false`, `cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`. This is the correct caller contract: a separate worker's scoped release/readback and synthetic task score do not silently become caller-level release confirmation or task success. Final test cleanup also read both keys up. The exact private Xvfb PID was absent after the run.

## Frozen conditions and environment

`CONDITIONS.json` was saved before execution. The run used one invocation, 8,000 ms delayed request, 1.0 s injected cancel-ack hold, owner-process tracing enabled, 5,000 ms terminal-result bound, display `:88`, 1024x768x24, and Xvfb TCP listening disabled. `environment.txt` and `pip-freeze.txt` retain runtime details and installed Python dependency versions. The environment was Ubuntu 24.04.3 LTS, native WSL (not WSLc), Python 3.12.3, python-xlib 0.33, Pillow 10.2.0, NumPy 1.26.4, and MCP 1.30.0. Xvfb was `2:21.1.12-1ubuntu1.8`, one Ubuntu package revision behind the earlier CI runner (`1ubuntu1.9`); the Xvfb binary SHA-256 is in `result.json`.

The test itself printed `Ran 1 test ... OK` and recorded exit value zero. The outer Bash wrapper then returned status 1 because the PowerShell here-string supplied a carriage return in its `exit` argument. That wrapper issue is recorded in `RUNNER_WRAPPER_STATUS.txt`; the test was not rerun. The decision comes from the retained unittest output, raw result, and raw-only audit.

## Scope

This is a scoped live X-server/caller validation of bounded cancel and separate release while the owner is blocked in `Display.sync()`, and of the liveness timestamp-order correction. Xvfb stayed responsive to independent connections. It does not test a stopped X server, physical desktop input, another backend, MAP01, model/provider behavior, a reliability population, or matched efficiency. The synthetic task oracle's `task_success=true` is local to its explicit property-and-keymap task; the MCP caller's `task_success` remains null.

No WSLc container, Docker, game, external GUI, or model was used. This run neither consumes nor renews any WSLc/MAP01 allocation. Do not treat native WSL results as WSLc portability evidence.
