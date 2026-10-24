# R29 — WSLc 2.95 s transaction-deadline counterexample

**Disposition: COUNTEREXAMPLE_SCOPED_TRANSACTION_DEADLINE (24/24 forensic audit checks).** At a preregistered 2,950 ms private-Xvfb pause, Xvfb resumed 101.597 ms before the exact 3,000 ms transaction deadline, yet the release worker reached its deadline and returned `unknown`. The standard caller's disconnect assertion failed as expected (`unknown` rather than `disconnected`), so the test stopped before independent task-effect/readback oracles. Runtime custody remained UNKNOWN and replay denied. No retry was made.

## Conditions and evidence

R29 used current-main source `058ab3c36092d5883d15bf44c7f0d4c573d2e763`, the unmodified public standard-caller test, the pinned Ubuntu 24.04 image digest, read-only source/dependency/stage/XKB mounts, a private no-network Xvfb, and a fresh unique WSLc session/container. Only the Xvfb pause changed from R28's 2,900 ms to 2,950 ms. The conditions were hash-pinned before session startup; the input-free Xlib/XRes PID/start-tick preflight passed before any test input.

- The retained pidfd resumed Xvfb after 2,950.258 ms. Resume preceded the exact transaction deadline by 101.597 ms.
- The transaction window was exactly 3,000 ms from admission. The release worker exited with `reason=transaction_deadline`; the transaction completion receipt arrived 2.765 ms after the deadline. The public cancel response itself returned in 305.944 ms, inside its separate response bound.
- The caller test failed at the expected assertion: disconnect status was `unknown` rather than `disconnected`. It returned 1, and the WSLc harness captured that failure.
- The test finalizer recorded `a`, `b`, and `c` all up after resuming Xvfb. This is teardown evidence after the failed release attempt; it is not a successful bounded-release receipt or an independent readback.
- Independent release readback, late-event horizon, old-task oracle, and fresh-generation task oracle did not run after the deadline assertion. No task-success claim is made.
- Exact container `4aacd59e211e3d9be36a0d8c355d740526d9fa806387aa7b17616329dbeac444`, pinned image, and session `ai-control-r29-c932a751d5144927b7356e4e8e41cf9e` were removed/terminated. The exact VHDX was recorded at 225,443,840 bytes with SHA-256 `060e862450585d182037bd05af9f50e739d4064255a2c9e052c8aed7018ed9ec`, then the exact storage path was removed and verified absent.

The forensic audit passed 24/24 checks for preregistration and source hashes, preflight ordering, exact pause, server resume/deadline ordering, asserted failure reason, conservative UNKNOWN/replay fence, non-execution of task oracles, finalizer state, and exact cleanup. Raw `result.json`, caller stderr, Xvfb/image/output records, JSONL WSLc receipts, original console log, storage manifest and audit are retained. The failure remains part of the result; do not replay R29.

## Scope and implication

R28 passed with a 2,900 ms pause and only 35.908 ms of measured transaction-deadline margin. R29 shows the current 3,000 ms transaction budget can expire even when Xvfb has resumed, if fewer than about 102 ms remain for supervised disconnect/release/readback in this run. This is a single synthetic-Xvfb boundary counterexample, not Windows desktop/MAP01 behavior or a reliability estimate. It identifies a narrow integration target: validate the server's transaction budget against worst-case resumed-server release/readback time while keeping the public cancel response separately bounded and retaining UNKNOWN/replay denial on timeout.
