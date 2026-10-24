# R30 — WSLc 2.95 s pause with a 4 s transaction budget

**Disposition: PASS_SCOPED_4S_TRANSACTION_RECOVERY (33/33 audit checks).** R30 reran the R29 2,950 ms private-Xvfb pause on patched source `aaa4fce67440fcd475e71e3134345f5649336f39`, with the internal guarded-cancellation transaction budget increased from 3.0 to 4.0 s. The release/readback receipt completed 995.384 ms before its deadline. The public cancel response remained 307.931 ms; the independent parent readback, late-event horizon, old-task oracle, and fresh-generation task oracle all passed. Runtime cancellation custody remains UNKNOWN and replay denied.

## Conditions and observations

Conditions were hash-pinned before startup. R30 used the unmodified public standard-caller Xvfb test, pinned Ubuntu 24.04 image digest, read-only source/dependency/stage/XKB mounts, private no-network Xvfb, and a new unique WSLc session/container. Compared with R29, the pause remained 2,950 ms and the caller/image conditions were unchanged; the source commit changes the transaction timeout default from 3.0 to 4.0 s and adds a Fake X regression for a finite release worker that completes after 3 s.

- The input-free Xlib/XRes PID/start-tick preflight passed before input. Xvfb was paused for 2,950.241 ms and resumed by its retained pidfd.
- The public cancel response returned in 307.931 ms. Supervisor XRes release/readback completed 3,004.616 ms after cancellation admission, inside the exact 4,000 ms transaction window with 995.384 ms remaining.
- An independent parent client saw all keys up at +3,164.535 ms. At +8,502.357 ms, all keys remained up and no delayed `b` event had appeared.
- The old synthetic task oracle passed with exactly one initial/final effect and all keys up at release and horizon. The separate fresh-generation task oracle passed exact-once (`[0] → [1]`, application effect `[0] → [3]`) and preserved the old cancellation fence.
- The standard-caller test and harness exited 0. Runtime cancellation still reports `cleanup_status=UNKNOWN`, `release_confirmed=false`, `replay_allowed=false`, and `task_success=null`; the independent oracles do not upgrade those runtime fields.
- Exact container `11b10a86fe437a51f4ce9d7b42b300d6f3e6297e241a62e308a32e4968e278c6`, image, and session `ai-control-r30-f222f351a0fc434b95c6c58dd3938e0b` were removed/terminated. The exact session VHDX was recorded at 224,395,264 bytes with SHA-256 `475b0f703e711e063b709534279c2ea491591e8b3e602f0453f95da9e78147a1`, then its exact storage path was removed and verified absent.

The independent audit passed 33/33 checks, including commit/source hashes, preregistration, the four-second transaction interval, release deadline margin, independent readbacks, both task oracles, the retained UNKNOWN fence, and exact cleanup. Raw caller result/event journal, image, Xvfb and test logs, full WSLc receipts, original console log, session-storage manifest and audit remain in this packet.

## Scope

R30 is a single synthetic private-Xvfb confirmation that the 4 s transaction allowance can finish the 2.95 s paused-server release path that exceeded R29's 3 s budget. It does not prove release during an indefinitely unavailable X server, Windows desktop/MAP01 behavior, production runtime task success, matched efficiency, or general reliability. Keep the public response bound separate from the transaction bound; an expired operation remains UNKNOWN and cannot be replayed.
