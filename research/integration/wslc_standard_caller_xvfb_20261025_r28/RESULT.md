# R28 — WSLc 2.9 s blocked-server deadline-boundary stress

**Disposition: PASS_SCOPED_DEADLINE_BOUNDARY_STRESS (29/29 audit checks).** The unmodified current-main standard caller completed its XRes release/readback receipt before the 3,000 ms transaction deadline during one 2,900 ms private-Xvfb pause. The receipt beat the deadline by 35.908 ms. This is one bounded synthetic-Xvfb sample; cancellation custody remains UNKNOWN and replay remains denied.

## Preregistered conditions and outcome

R28 used source `058ab3c36092d5883d15bf44c7f0d4c573d2e763`, the unmodified `runtime.cli_v1.test_mcp_xvfb_blocked_release_integration`, the pinned Ubuntu 24.04 image digest, read-only source/dependency/stage/XKB mounts, private no-network Xvfb, and a fresh, unique WSLc session/container/storage path. Only the Xvfb pause changed from R26's 2,800 ms to 2,900 ms. The condition file was preregistered and hash-pinned before session startup; the input-free Xlib/XRes PID/start-tick gate passed before the test emitted input.

- Xvfb was stopped through the retained pidfd for the requested 2,900 ms. The public cancel response took 305.590 ms.
- Supervisor release/readback completed 2,964.092 ms after the cancellation transaction's admission point and 35.908 ms before its exact deadline. The independent parent readback saw all keys up at +3,099.270 ms after cancellation began, within the preregistered +5,000 ms bound.
- At +8,502.138 ms, the late-event horizon showed `a`, `b`, and `c` all up and no delayed `b` event.
- The old synthetic task retained exact effect count 1 and passed its separate oracle. The fresh-generation task went from 0 to exactly 1 effect and passed its separate exact-effect oracle.
- The public caller test and WSLc harness both exited 0. Exact container `d256176a4792347c7c235aa10132085d93de0baaa51a7d1eee94b6eb29d25df1`, image, and session `ai-control-r28-44dc9bab4f5f433f87092e3c9f791b60` were removed/terminated. The exact session disk was recorded at 224,395,264 bytes with SHA-256 `3f97d63f0bdde0f6bf9b25c91b50c1dc0f7bb99bf03ad428902ba3bd5b48c310`, then its exact path was removed and verified absent.

The independent audit passed 29/29 checks for condition/preregistration hashes, source and runner pins, requested pause, deadline, parent readback, old/fresh task oracles, late-event horizon, UNKNOWN fence, and exact cleanup. Raw caller result, event journal, image, Xvfb and caller logs, full WSLc JSONL receipts, original harness console log, session-storage manifest, and audit are retained alongside the preregistration.

## Scope

R28 extends the WSLc synthetic-Xvfb stress boundary from R26's 2.8 s to 2.9 s and leaves only 35.9 ms of measured deadline margin in this sample. It does not establish behavior under a longer/unbounded platform outage, Win32 desktop/MAP01 behavior, production task success, matched efficiency, or broad reliability. `cleanup_status=UNKNOWN`, `release_confirmed=false`, `replay_allowed=false`, and `task_success=null` remain the runtime's conservative custody outcome. No retry was made.
